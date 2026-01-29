import { useState, useEffect } from 'react';
import type { TaskCreate, Channel } from '@/types';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import { Switch } from '@/components/ui/Switch';
import { Checkbox } from '@/components/ui/Checkbox';
import { Badge } from '@/components/ui/Badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/Dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import { api } from '@/lib/api';
import { useSkillsStore, useNotificationsStore } from '@/stores';
import { Bell, X, ChevronDown } from 'lucide-react';

// Provider icons/colors for visual distinction
const PROVIDER_CONFIG: Record<string, { color: string; label: string }> = {
  telegram: { color: 'bg-blue-500', label: 'Telegram' },
  discord: { color: 'bg-indigo-500', label: 'Discord' },
  slack: { color: 'bg-green-500', label: 'Slack' },
  teams: { color: 'bg-purple-500', label: 'Teams' },
};

interface TaskFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: TaskCreate) => Promise<void>;
  initialData?: Partial<TaskCreate>;
  isEdit?: boolean;
}

const NOTIFICATION_EVENTS = [
  { id: 'task_start', label: 'On Start' },
  { id: 'task_success', label: 'On Success' },
  { id: 'task_failure', label: 'On Failure' },
] as const;

const CRON_EXAMPLES = [
  { expression: '0 9 * * *', label: 'Daily 9am' },
  { expression: '0 9 * * 1-5', label: 'Weekdays 9am' },
  { expression: '*/15 * * * *', label: 'Every 15 min' },
  { expression: '0 */2 * * *', label: 'Every 2 hours' },
  { expression: '0 0 * * 0', label: 'Sunday midnight' },
  { expression: '0 8 1 * *', label: '1st of month' },
] as const;

export function TaskForm({ open, onOpenChange, onSubmit, initialData, isEdit }: TaskFormProps) {
  const { skills, fetchSkills } = useSkillsStore();
  const { channels, fetchChannels } = useNotificationsStore();
  const [loading, setLoading] = useState(false);
  const [cronValid, setCronValid] = useState<boolean | null>(null);
  const [cronDescription, setCronDescription] = useState<string>('');

  const [formData, setFormData] = useState<TaskCreate>({
    name: '',
    schedule: '',
    working_dir: '',
    skill: null,
    prompt: null,
    model: 'sonnet',
    timeout: 300,
    enabled: true,
    notifications: null,
    ...initialData,
  });

  // Notification UI state
  const [selectedChannels, setSelectedChannels] = useState<string[]>(
    initialData?.notifications?.channels || []
  );
  const [selectedEvents, setSelectedEvents] = useState<string[]>(
    initialData?.notifications?.events || ['task_failure']
  );
  const [includeOutput, setIncludeOutput] = useState<boolean>(
    initialData?.notifications?.include_output || false
  );

  useEffect(() => {
    if (open) {
      fetchSkills();
      fetchChannels();
    }
  }, [open, fetchSkills, fetchChannels]);

  // Sync notification state to formData
  useEffect(() => {
    if (selectedChannels.length > 0) {
      setFormData((prev) => ({
        ...prev,
        notifications: {
          channels: selectedChannels,
          events: selectedEvents,
          include_output: includeOutput,
        },
      }));
    } else {
      setFormData((prev) => ({ ...prev, notifications: null }));
    }
  }, [selectedChannels, selectedEvents, includeOutput]);

  useEffect(() => {
    if (initialData) {
      setFormData((prev) => ({ ...prev, ...initialData }));
      // Also update notification state
      setSelectedChannels(initialData.notifications?.channels || []);
      setSelectedEvents(initialData.notifications?.events || ['task_failure']);
      setIncludeOutput(initialData.notifications?.include_output || false);
    }
  }, [initialData]);

  const validateCron = async (expression: string) => {
    if (!expression) {
      setCronValid(null);
      setCronDescription('');
      return;
    }
    try {
      const result = await api.cron.validate(expression);
      setCronValid(result.valid);
      setCronDescription(result.description || result.error || '');
    } catch {
      setCronValid(false);
      setCronDescription('Failed to validate');
    }
  };

  const handleScheduleChange = (value: string) => {
    setFormData((prev) => ({ ...prev, schedule: value }));
    validateCron(value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit(formData);
      onOpenChange(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit Task' : 'Create New Task'}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="name">Task Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="daily-review"
              required
            />
          </div>

          {/* Schedule */}
          <div className="space-y-2">
            <Label htmlFor="schedule">Schedule (CRON Expression)</Label>
            <Input
              id="schedule"
              value={formData.schedule}
              onChange={(e) => handleScheduleChange(e.target.value)}
              placeholder="0 9 * * 1-5"
              required
              className={cronValid === false ? 'border-destructive' : cronValid === true ? 'border-success' : ''}
            />
            {cronDescription && (
              <p className={`text-sm ${cronValid ? 'text-success' : 'text-destructive'}`}>
                {cronDescription}
              </p>
            )}
            <div className="flex flex-wrap gap-1.5 pt-1">
              <span className="text-xs text-muted-foreground">Examples:</span>
              {CRON_EXAMPLES.map((example) => (
                <button
                  key={example.expression}
                  type="button"
                  onClick={() => handleScheduleChange(example.expression)}
                  className="text-xs px-2 py-0.5 rounded-full bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground transition-colors"
                  title={example.expression}
                >
                  {example.label}
                </button>
              ))}
            </div>
          </div>

          {/* Working Directory */}
          <div className="space-y-2">
            <Label htmlFor="working_dir">Working Directory</Label>
            <Input
              id="working_dir"
              value={formData.working_dir}
              onChange={(e) => setFormData((prev) => ({ ...prev, working_dir: e.target.value }))}
              placeholder="/path/to/project"
              required
            />
          </div>

          {/* Skill or Prompt */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="skill">Skill</Label>
              <Select
                value={formData.skill || 'none'}
                onValueChange={(value) =>
                  setFormData((prev) => ({
                    ...prev,
                    skill: value === 'none' ? null : value,
                    prompt: value !== 'none' ? null : prev.prompt,
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a skill" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No skill (use prompt)</SelectItem>
                  {skills.map((skill) => (
                    <SelectItem key={skill.name} value={skill.name}>
                      {skill.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="model">Model</Label>
              <Select
                value={formData.model}
                onValueChange={(value: 'haiku' | 'sonnet' | 'opus') =>
                  setFormData((prev) => ({ ...prev, model: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="haiku">Haiku (Fast)</SelectItem>
                  <SelectItem value="sonnet">Sonnet (Balanced)</SelectItem>
                  <SelectItem value="opus">Opus (Powerful)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Prompt (if no skill) */}
          {!formData.skill && (
            <div className="space-y-2">
              <Label htmlFor="prompt">Prompt</Label>
              <Textarea
                id="prompt"
                value={formData.prompt || ''}
                onChange={(e) => setFormData((prev) => ({ ...prev, prompt: e.target.value }))}
                placeholder="Enter the task prompt..."
                rows={4}
              />
            </div>
          )}

          {/* Timeout and Enabled */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="timeout">Timeout (seconds)</Label>
              <Input
                id="timeout"
                type="number"
                value={formData.timeout}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, timeout: parseInt(e.target.value) || 300 }))
                }
                min={30}
                max={3600}
              />
            </div>

            <div className="flex items-center space-x-2 pt-6">
              <Switch
                id="enabled"
                checked={formData.enabled}
                onCheckedChange={(checked) =>
                  setFormData((prev) => ({ ...prev, enabled: checked }))
                }
              />
              <Label htmlFor="enabled">Enabled</Label>
            </div>
          </div>

          {/* Notifications */}
          <div className="space-y-4 border-t pt-4">
            <div className="flex items-center gap-2">
              <Bell className="h-4 w-4" />
              <Label className="text-base font-medium">Notifications</Label>
            </div>

            {channels.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No notification channels configured. Go to Settings to add one.
              </p>
            ) : (
              <>
                {/* Channel Selection with Dropdown */}
                <div className="space-y-3">
                  <Label className="text-sm">Send notifications to:</Label>

                  {/* Multi-select Dropdown */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="outline" className="w-full justify-between">
                        <span className="text-muted-foreground">
                          {selectedChannels.length === 0
                            ? 'Select channels...'
                            : `${selectedChannels.length} channel${selectedChannels.length > 1 ? 's' : ''} selected`}
                        </span>
                        <ChevronDown className="h-4 w-4 opacity-50" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="w-72 max-h-64 overflow-y-auto">
                      {/* Group channels by provider */}
                      {Object.entries(
                        channels
                          .filter((ch) => ch.enabled)
                          .reduce((acc, channel) => {
                            const provider = channel.provider;
                            if (!acc[provider]) acc[provider] = [];
                            acc[provider].push(channel);
                            return acc;
                          }, {} as Record<string, Channel[]>)
                      ).map(([provider, providerChannels], idx) => (
                        <div key={provider}>
                          {idx > 0 && <DropdownMenuSeparator />}
                          <DropdownMenuLabel className="flex items-center gap-2">
                            <span
                              className={`w-2 h-2 rounded-full ${PROVIDER_CONFIG[provider]?.color || 'bg-gray-500'}`}
                            />
                            {PROVIDER_CONFIG[provider]?.label || provider}
                          </DropdownMenuLabel>
                          {providerChannels.map((channel) => (
                            <DropdownMenuCheckboxItem
                              key={channel.id}
                              checked={selectedChannels.includes(channel.id)}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  setSelectedChannels((prev) => [...prev, channel.id]);
                                } else {
                                  setSelectedChannels((prev) =>
                                    prev.filter((id) => id !== channel.id)
                                  );
                                }
                              }}
                            >
                              {channel.name}
                            </DropdownMenuCheckboxItem>
                          ))}
                        </div>
                      ))}
                    </DropdownMenuContent>
                  </DropdownMenu>

                  {/* Selected Channels as Badges */}
                  {selectedChannels.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {selectedChannels.map((channelId) => {
                        const channel = channels.find((c) => c.id === channelId);
                        if (!channel) return null;
                        const providerConfig = PROVIDER_CONFIG[channel.provider];
                        return (
                          <Badge
                            key={channelId}
                            variant="secondary"
                            className="pl-2 pr-1 py-1 flex items-center gap-1"
                          >
                            <span
                              className={`w-2 h-2 rounded-full ${providerConfig?.color || 'bg-gray-500'}`}
                            />
                            <span>{channel.name}</span>
                            <button
                              type="button"
                              onClick={() =>
                                setSelectedChannels((prev) =>
                                  prev.filter((id) => id !== channelId)
                                )
                              }
                              className="ml-1 rounded-full hover:bg-muted p-0.5"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </Badge>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Event Selection - only show if channels are selected */}
                {selectedChannels.length > 0 && (
                  <div className="space-y-3 pt-2">
                    <Label className="text-sm">Notify on:</Label>
                    <div className="flex flex-wrap gap-2">
                      {NOTIFICATION_EVENTS.map((event) => {
                        const isSelected = selectedEvents.includes(event.id);
                        return (
                          <button
                            key={event.id}
                            type="button"
                            onClick={() => {
                              if (isSelected) {
                                setSelectedEvents((prev) =>
                                  prev.filter((id) => id !== event.id)
                                );
                              } else {
                                setSelectedEvents((prev) => [...prev, event.id]);
                              }
                            }}
                            className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
                              isSelected
                                ? 'bg-primary text-primary-foreground border-primary'
                                : 'bg-background hover:bg-muted border-input'
                            }`}
                          >
                            {event.label}
                          </button>
                        );
                      })}
                    </div>

                    <div className="flex items-center space-x-2 pt-1">
                      <Checkbox
                        id="include-output"
                        checked={includeOutput}
                        onCheckedChange={(checked) => setIncludeOutput(checked === true)}
                      />
                      <Label htmlFor="include-output" className="text-sm font-normal">
                        Include task output in notification
                      </Label>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading || cronValid === false}>
              {loading ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Task'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
