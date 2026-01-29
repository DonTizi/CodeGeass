import { useState, useEffect } from 'react';
import type { TaskCreate } from '@/types';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import { Switch } from '@/components/ui/Switch';
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
import { api } from '@/lib/api';
import { useSkillsStore } from '@/stores';

interface TaskFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: TaskCreate) => Promise<void>;
  initialData?: Partial<TaskCreate>;
  isEdit?: boolean;
}

export function TaskForm({ open, onOpenChange, onSubmit, initialData, isEdit }: TaskFormProps) {
  const { skills, fetchSkills } = useSkillsStore();
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
    ...initialData,
  });

  useEffect(() => {
    if (open) {
      fetchSkills();
    }
  }, [open, fetchSkills]);

  useEffect(() => {
    if (initialData) {
      setFormData((prev) => ({ ...prev, ...initialData }));
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
