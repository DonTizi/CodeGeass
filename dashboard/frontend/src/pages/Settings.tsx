import { useEffect, useState } from 'react';
import { Bell, Plus, Trash2, TestTube2, Power, PowerOff } from 'lucide-react';
import { useNotificationsStore } from '@/stores';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/Dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { useToast } from '@/components/ui/Toaster';
import type { ChannelCreate } from '@/types';

export function Settings() {
  const {
    channels,
    providers,
    loading,
    fetchChannels,
    fetchProviders,
    createChannel,
    deleteChannel,
    enableChannel,
    disableChannel,
    testChannel,
    sendTestMessage,
  } = useNotificationsStore();

  const { toast } = useToast();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [testingChannel, setTestingChannel] = useState<string | null>(null);

  useEffect(() => {
    fetchChannels();
    fetchProviders();
  }, [fetchChannels, fetchProviders]);

  const selectedProviderInfo = providers.find((p) => p.name === selectedProvider);

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);
    setFormData({});
  };

  const handleCreateChannel = async () => {
    if (!selectedProvider || !formData.name) return;

    const providerInfo = providers.find((p) => p.name === selectedProvider);
    if (!providerInfo) return;

    // Build credentials object
    const credentials: Record<string, string> = {};
    for (const field of providerInfo.required_credentials) {
      if (formData[field.name]) {
        credentials[field.name] = formData[field.name];
      }
    }

    // Build config object
    const config: Record<string, unknown> = {};
    for (const field of providerInfo.required_config) {
      if (formData[field.name]) {
        config[field.name] = formData[field.name];
      }
    }
    // Include optional config fields if provided
    for (const field of providerInfo.optional_config) {
      if (formData[field.name]) {
        config[field.name] = formData[field.name];
      }
    }

    const data: ChannelCreate = {
      name: formData.name,
      provider: selectedProvider,
      credentials,
      config,
    };

    try {
      await createChannel(data);
      toast({
        title: 'Channel created',
        description: `${formData.name} has been created successfully.`,
      });
      setShowAddDialog(false);
      setSelectedProvider('');
      setFormData({});
    } catch (e) {
      toast({
        title: 'Error',
        description: e instanceof Error ? e.message : 'Failed to create channel',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteChannel = async (channelId: string, channelName: string) => {
    if (!confirm(`Delete channel "${channelName}"?`)) return;

    try {
      await deleteChannel(channelId);
      toast({
        title: 'Channel deleted',
        description: `${channelName} has been deleted.`,
      });
    } catch (e) {
      toast({
        title: 'Error',
        description: e instanceof Error ? e.message : 'Failed to delete channel',
        variant: 'destructive',
      });
    }
  };

  const handleToggleChannel = async (channelId: string, enabled: boolean) => {
    try {
      if (enabled) {
        await disableChannel(channelId);
      } else {
        await enableChannel(channelId);
      }
    } catch (e) {
      toast({
        title: 'Error',
        description: e instanceof Error ? e.message : 'Failed to toggle channel',
        variant: 'destructive',
      });
    }
  };

  const handleTestChannel = async (channelId: string) => {
    setTestingChannel(channelId);
    try {
      // First test connection
      const result = await testChannel(channelId);
      if (!result.success) {
        toast({
          title: 'Test failed',
          description: result.message,
          variant: 'destructive',
        });
        return;
      }

      // Then send a test message
      await sendTestMessage(channelId);
      toast({
        title: 'Test successful',
        description: `${result.message} - Test message sent!`,
      });
    } catch (e) {
      toast({
        title: 'Test failed',
        description: e instanceof Error ? e.message : 'Failed to test channel',
        variant: 'destructive',
      });
    } finally {
      setTestingChannel(null);
    }
  };

  const getProviderDisplayName = (provider: string) => {
    const info = providers.find((p) => p.name === provider);
    return info?.display_name || provider;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">
            Configure notifications and other settings
          </p>
        </div>
      </div>

      {/* Notification Channels Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              <CardTitle>Notification Channels</CardTitle>
            </div>
            <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Channel
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                  <DialogTitle>Add Notification Channel</DialogTitle>
                  <DialogDescription>
                    Configure a new notification channel to receive task alerts.{' '}
                    <a
                      href="https://dontizi.github.io/CodeGeass/latest/guides/setup-notifications/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary underline hover:text-primary/80"
                    >
                      Setup guide →
                    </a>
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="provider">Provider</Label>
                    <Select value={selectedProvider} onValueChange={handleProviderChange}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a provider" />
                      </SelectTrigger>
                      <SelectContent>
                        {providers.map((provider) => (
                          <SelectItem key={provider.name} value={provider.name}>
                            {provider.display_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {selectedProviderInfo && (
                    <>
                      <div className="grid gap-2">
                        <Label htmlFor="name">Channel Name</Label>
                        <Input
                          id="name"
                          value={formData.name || ''}
                          onChange={(e) =>
                            setFormData({ ...formData, name: e.target.value })
                          }
                          placeholder="My Telegram Channel"
                        />
                      </div>

                      {selectedProviderInfo.required_credentials.map((field) => (
                        <div key={field.name} className="grid gap-2">
                          <Label htmlFor={field.name}>{field.description}</Label>
                          <Input
                            id={field.name}
                            type={field.sensitive ? 'password' : 'text'}
                            value={formData[field.name] || ''}
                            onChange={(e) =>
                              setFormData({ ...formData, [field.name]: e.target.value })
                            }
                            placeholder={field.name}
                          />
                        </div>
                      ))}

                      {selectedProviderInfo.required_config.map((field) => (
                        <div key={field.name} className="grid gap-2">
                          <Label htmlFor={field.name}>{field.description}</Label>
                          <Input
                            id={field.name}
                            value={formData[field.name] || ''}
                            onChange={(e) =>
                              setFormData({ ...formData, [field.name]: e.target.value })
                            }
                            placeholder={field.name}
                          />
                        </div>
                      ))}

                      {selectedProviderInfo.optional_config.length > 0 && (
                        <>
                          {selectedProviderInfo.optional_config.map((field) => (
                            <div key={field.name} className="grid gap-2">
                              <Label htmlFor={field.name} className="text-muted-foreground">
                                {field.description} (optional)
                              </Label>
                              <Input
                                id={field.name}
                                value={formData[field.name] || ''}
                                onChange={(e) =>
                                  setFormData({ ...formData, [field.name]: e.target.value })
                                }
                                placeholder={field.default?.toString() || field.name}
                              />
                            </div>
                          ))}
                        </>
                      )}
                    </>
                  )}
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowAddDialog(false)}>
                    Cancel
                  </Button>
                  <Button
                    onClick={handleCreateChannel}
                    disabled={!selectedProvider || !formData.name || loading}
                  >
                    Create Channel
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
          <CardDescription>
            Configure channels to receive notifications when tasks start, complete, or fail.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {channels.length === 0 ? (
            <div className="text-center py-6 text-muted-foreground">
              <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No notification channels configured.</p>
              <p className="text-sm">Add a channel to start receiving task notifications.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {channels.map((channel) => (
                <div
                  key={channel.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{channel.name}</span>
                        <Badge variant={channel.enabled ? 'default' : 'secondary'}>
                          {channel.enabled ? 'Enabled' : 'Disabled'}
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {getProviderDisplayName(channel.provider)} &bull; ID: {channel.id}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTestChannel(channel.id)}
                      disabled={testingChannel === channel.id}
                    >
                      <TestTube2 className="h-4 w-4 mr-1" />
                      {testingChannel === channel.id ? 'Testing...' : 'Test'}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleToggleChannel(channel.id, channel.enabled)}
                    >
                      {channel.enabled ? (
                        <>
                          <PowerOff className="h-4 w-4 mr-1" />
                          Disable
                        </>
                      ) : (
                        <>
                          <Power className="h-4 w-4 mr-1" />
                          Enable
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteChannel(channel.id, channel.name)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
