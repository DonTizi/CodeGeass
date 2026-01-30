"""Approval management CLI commands."""

import asyncio

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from codegeass.cli.main import Context, pass_context
from codegeass.execution.plan_approval import ApprovalStatus

console = Console()


@click.group()
def approval() -> None:
    """Manage plan approvals for plan-mode tasks."""
    pass


@approval.command("list")
@click.option("--pending", "-p", is_flag=True, help="Show only pending approvals")
@click.option(
    "--status",
    "-s",
    help="Filter by status (pending, approved, completed, cancelled, expired, failed)",
)
@pass_context
def list_approvals(ctx: Context, pending: bool, status: str | None) -> None:
    """List plan approvals."""
    all_approvals = ctx.approval_repo.find_all()

    if pending:
        approvals = ctx.approval_repo.find_pending()
    elif status:
        try:
            status_enum = ApprovalStatus(status.lower())
            approvals = ctx.approval_repo.find_by_status(status_enum)
        except ValueError:
            console.print(f"[red]Invalid status: {status}[/red]")
            console.print(f"Valid statuses: {', '.join(s.value for s in ApprovalStatus)}")
            raise SystemExit(1)
    else:
        approvals = all_approvals

    if not approvals:
        console.print("[yellow]No approvals found.[/yellow]")
        return

    table = Table(title="Plan Approvals")
    table.add_column("ID", style="cyan")
    table.add_column("Task")
    table.add_column("Status")
    table.add_column("Iteration")
    table.add_column("Created")
    table.add_column("Expires")

    for a in approvals:
        # Color status
        status_color = {
            ApprovalStatus.PENDING: "yellow",
            ApprovalStatus.APPROVED: "blue",
            ApprovalStatus.EXECUTING: "blue",
            ApprovalStatus.COMPLETED: "green",
            ApprovalStatus.CANCELLED: "dim",
            ApprovalStatus.EXPIRED: "red",
            ApprovalStatus.FAILED: "red",
        }.get(a.status, "white")

        status_str = f"[{status_color}]{a.status.value}[/{status_color}]"

        # Mark expired pending approvals
        if a.status == ApprovalStatus.PENDING and a.is_expired:
            status_str = "[red]expired[/red]"

        table.add_row(
            a.id,
            a.task_name,
            status_str,
            f"{a.iteration}/{a.max_iterations}",
            a.created_at[:16],
            a.expires_at[:16] if a.status == ApprovalStatus.PENDING else "-",
        )

    console.print(table)

    # Show summary
    pending_count = len(
        [a for a in all_approvals if a.status == ApprovalStatus.PENDING and not a.is_expired]
    )
    console.print(
        f"\n[bold]Total:[/bold] {len(all_approvals)} | [bold]Pending:[/bold] {pending_count}"
    )


@approval.command("show")
@click.argument("approval_id", required=False)
@click.option("--task", "-t", help="Find approval by task ID or name")
@pass_context
def show_approval(ctx: Context, approval_id: str | None, task: str | None) -> None:
    """Show details for a specific approval."""
    if not approval_id and not task:
        console.print("[red]Specify either APPROVAL_ID or --task[/red]")
        raise SystemExit(1)

    if task:
        # Find by task
        approval = ctx.approval_repo.find_by_task_id(task)
        if not approval:
            # Try to find task by name
            task_obj = ctx.task_repo.find_by_name(task)
            if task_obj:
                approval = ctx.approval_repo.find_by_task_id(task_obj.id)
    else:
        approval = ctx.approval_repo.find_by_id(approval_id)

    if not approval:
        console.print(f"[red]Approval not found: {approval_id}[/red]")
        raise SystemExit(1)

    # Status color
    status_color = {
        ApprovalStatus.PENDING: "yellow",
        ApprovalStatus.APPROVED: "blue",
        ApprovalStatus.EXECUTING: "blue",
        ApprovalStatus.COMPLETED: "green",
        ApprovalStatus.CANCELLED: "dim",
        ApprovalStatus.EXPIRED: "red",
        ApprovalStatus.FAILED: "red",
    }.get(approval.status, "white")

    # Build info panel
    info = f"""[bold]ID:[/bold] {approval.id}
[bold]Task:[/bold] {approval.task_name} ({approval.task_id})
[bold]Session ID:[/bold] {approval.session_id}
[bold]Status:[/bold] [{status_color}]{approval.status.value}[/{status_color}]
[bold]Iteration:[/bold] {approval.iteration}/{approval.max_iterations}
[bold]Created:[/bold] {approval.created_at}
[bold]Expires:[/bold] {approval.expires_at}
[bold]Working Dir:[/bold] {approval.working_dir}"""

    if approval.worktree_path:
        info += f"\n[bold]Worktree:[/bold] {approval.worktree_path}"

    if approval.error:
        info += f"\n[bold]Error:[/bold] [red]{approval.error}[/red]"

    console.print(Panel(info, title=f"Approval: {approval.id}"))

    # Show plan
    console.print("\n[bold]Plan:[/bold]")
    console.print(
        Panel(
            approval.plan_text[:2000] + ("..." if len(approval.plan_text) > 2000 else ""),
            border_style="dim",
        )
    )

    # Show feedback history
    if approval.feedback_history:
        console.print("\n[bold]Feedback History:[/bold]")
        for i, entry in enumerate(approval.feedback_history, 1):
            console.print(f"\n[cyan]#{i}[/cyan] ({entry.timestamp[:16]})")
            console.print(f"  [bold]Feedback:[/bold] {entry.feedback}")
            if entry.plan_response:
                console.print(f"  [bold]Response:[/bold] {entry.plan_response[:200]}...")

    # Show final output if completed
    if approval.final_output:
        console.print("\n[bold]Final Output:[/bold]")
        output_preview = approval.final_output[:1000]
        if len(approval.final_output) > 1000:
            output_preview += "\n\n[dim]... (truncated)[/dim]"
        console.print(Panel(output_preview, border_style="green"))


@approval.command("approve")
@click.argument("approval_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@pass_context
def approve_plan(ctx: Context, approval_id: str, yes: bool) -> None:
    """Approve a pending plan and execute it."""
    from codegeass.execution.plan_service import PlanApprovalService

    approval = ctx.approval_repo.find_by_id(approval_id)

    if not approval:
        console.print(f"[red]Approval not found: {approval_id}[/red]")
        raise SystemExit(1)

    if approval.status != ApprovalStatus.PENDING:
        console.print(f"[red]Approval is not pending: {approval.status.value}[/red]")
        raise SystemExit(1)

    if approval.is_expired:
        console.print("[red]Approval has expired.[/red]")
        raise SystemExit(1)

    # Show plan and confirm
    if not yes:
        console.print(f"[bold]Task:[/bold] {approval.task_name}")
        console.print(f"[bold]Plan preview:[/bold]\n{approval.plan_text[:500]}...")
        if not click.confirm("\nApprove and execute this plan?"):
            console.print("Cancelled")
            return

    console.print("[yellow]Approving and executing plan...[/yellow]")

    # Create service and execute
    plan_service = PlanApprovalService(ctx.approval_repo, ctx.channel_repo)

    try:
        result = asyncio.run(plan_service.handle_approval(approval_id))

        if result and result.is_success:
            console.print("[green]Plan executed successfully![/green]")
            console.print(f"Duration: {result.duration_seconds:.1f}s")
        elif result:
            console.print(f"[red]Execution failed: {result.error}[/red]")
            raise SystemExit(1)
        else:
            console.print("[red]Failed to approve plan.[/red]")
            raise SystemExit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@approval.command("discuss")
@click.argument("approval_id")
@click.option("--feedback", "-f", required=True, help="Feedback to send to Claude")
@pass_context
def discuss_plan(ctx: Context, approval_id: str, feedback: str) -> None:
    """Provide feedback on a plan for iterative refinement."""
    from codegeass.execution.plan_service import PlanApprovalService

    approval = ctx.approval_repo.find_by_id(approval_id)

    if not approval:
        console.print(f"[red]Approval not found: {approval_id}[/red]")
        raise SystemExit(1)

    if approval.status != ApprovalStatus.PENDING:
        console.print(f"[red]Approval is not pending: {approval.status.value}[/red]")
        raise SystemExit(1)

    if not approval.can_discuss:
        console.print(f"[red]Max iterations reached ({approval.max_iterations})[/red]")
        raise SystemExit(1)

    iter_info = f"{approval.iteration + 1}/{approval.max_iterations}"
    console.print(f"[yellow]Sending feedback (iteration {iter_info})...[/yellow]")

    # Create service and send feedback
    plan_service = PlanApprovalService(ctx.approval_repo, ctx.channel_repo)

    try:
        updated = asyncio.run(plan_service.handle_discuss(approval_id, feedback))

        if updated:
            console.print("[green]New plan generated![/green]")
            console.print("\n[bold]Updated Plan:[/bold]")
            console.print(Panel(updated.plan_text[:2000], border_style="dim"))
        else:
            console.print("[red]Failed to process feedback.[/red]")
            raise SystemExit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@approval.command("cancel")
@click.argument("approval_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@pass_context
def cancel_approval(ctx: Context, approval_id: str, yes: bool) -> None:
    """Cancel a pending plan."""
    from codegeass.execution.plan_service import PlanApprovalService

    approval = ctx.approval_repo.find_by_id(approval_id)

    if not approval:
        console.print(f"[red]Approval not found: {approval_id}[/red]")
        raise SystemExit(1)

    if approval.status != ApprovalStatus.PENDING:
        console.print(f"[red]Approval is not pending: {approval.status.value}[/red]")
        raise SystemExit(1)

    if not yes:
        if not click.confirm(f"Cancel approval for task '{approval.task_name}'?"):
            console.print("Cancelled")
            return

    plan_service = PlanApprovalService(ctx.approval_repo, ctx.channel_repo)

    try:
        success = asyncio.run(plan_service.handle_cancel(approval_id))

        if success:
            console.print("[green]Approval cancelled.[/green]")
        else:
            console.print("[red]Failed to cancel approval.[/red]")
            raise SystemExit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@approval.command("cleanup")
@click.option("--expired", is_flag=True, help="Mark expired approvals")
@click.option("--old", type=int, help="Remove completed/cancelled approvals older than N days")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@pass_context
def cleanup_approvals(ctx: Context, expired: bool, old: int | None, yes: bool) -> None:
    """Cleanup old or expired approvals."""
    if not expired and old is None:
        console.print("[yellow]Specify --expired and/or --old <days>[/yellow]")
        return

    if not yes:
        actions = []
        if expired:
            actions.append("mark expired approvals")
        if old:
            actions.append(f"remove approvals older than {old} days")
        if not click.confirm(f"This will: {', '.join(actions)}. Continue?"):
            console.print("Cancelled")
            return

    total_cleaned = 0

    if expired:
        count = ctx.approval_repo.cleanup_expired()
        console.print(f"Marked [cyan]{count}[/cyan] approvals as expired")
        total_cleaned += count

    if old:
        count = ctx.approval_repo.cleanup_old(old)
        console.print(f"Removed [cyan]{count}[/cyan] old approvals")
        total_cleaned += count

    if total_cleaned == 0:
        console.print("[green]Nothing to cleanup.[/green]")
    else:
        console.print(f"[green]Cleaned up {total_cleaned} approvals.[/green]")


@approval.command("stats")
@pass_context
def stats_approvals(ctx: Context) -> None:
    """Show approval statistics."""
    all_approvals = ctx.approval_repo.find_all()

    if not all_approvals:
        console.print("[yellow]No approvals found.[/yellow]")
        return

    # Count by status
    stats = {s: 0 for s in ApprovalStatus}
    for approval in all_approvals:
        stats[approval.status] += 1

    # Check for expired pending
    expired_pending = len(
        [a for a in all_approvals if a.status == ApprovalStatus.PENDING and a.is_expired]
    )

    table = Table(title="Approval Statistics")
    table.add_column("Status")
    table.add_column("Count", justify="right")

    status_colors = {
        ApprovalStatus.PENDING: "yellow",
        ApprovalStatus.APPROVED: "blue",
        ApprovalStatus.EXECUTING: "blue",
        ApprovalStatus.COMPLETED: "green",
        ApprovalStatus.CANCELLED: "dim",
        ApprovalStatus.EXPIRED: "red",
        ApprovalStatus.FAILED: "red",
    }

    for status, count in stats.items():
        if count > 0:
            color = status_colors.get(status, "white")
            table.add_row(f"[{color}]{status.value}[/{color}]", str(count))

    console.print(table)

    # Summary
    total = len(all_approvals)
    completed = stats[ApprovalStatus.COMPLETED]
    failed = stats[ApprovalStatus.FAILED]
    success_rate = (completed / (completed + failed) * 100) if (completed + failed) > 0 else 0

    console.print(f"\n[bold]Total:[/bold] {total}")
    console.print(f"[bold]Success Rate:[/bold] {success_rate:.1f}% (of executed)")

    if expired_pending > 0:
        console.print(f"[yellow]Note: {expired_pending} pending approvals have expired[/yellow]")


@approval.command("delete")
@click.argument("approval_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@pass_context
def delete_approval(ctx: Context, approval_id: str, yes: bool) -> None:
    """Delete an approval record."""
    approval = ctx.approval_repo.find_by_id(approval_id)

    if not approval:
        console.print(f"[red]Approval not found: {approval_id}[/red]")
        raise SystemExit(1)

    if approval.status == ApprovalStatus.PENDING:
        console.print(
            "[yellow]Warning: This approval is still pending. Use 'cancel' first.[/yellow]"
        )

    if not yes:
        if not click.confirm(f"Delete approval '{approval_id}' for task '{approval.task_name}'?"):
            console.print("Cancelled")
            return

    if ctx.approval_repo.delete(approval_id):
        console.print(f"[green]Deleted approval: {approval_id}[/green]")
    else:
        console.print(f"[red]Failed to delete approval: {approval_id}[/red]")
        raise SystemExit(1)
