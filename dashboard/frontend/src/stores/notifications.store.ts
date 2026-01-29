import { create } from 'zustand';
import type { Channel, ChannelCreate, ChannelUpdate, ProviderInfo, TestResult } from '@/types';
import { api } from '@/lib/api';

interface NotificationsState {
  channels: Channel[];
  providers: ProviderInfo[];
  selectedChannel: Channel | null;
  loading: boolean;
  error: string | null;

  fetchChannels: () => Promise<void>;
  fetchProviders: () => Promise<void>;
  fetchChannel: (channelId: string) => Promise<void>;
  createChannel: (data: ChannelCreate) => Promise<Channel>;
  updateChannel: (channelId: string, data: ChannelUpdate) => Promise<Channel>;
  deleteChannel: (channelId: string) => Promise<void>;
  enableChannel: (channelId: string) => Promise<void>;
  disableChannel: (channelId: string) => Promise<void>;
  testChannel: (channelId: string) => Promise<TestResult>;
  sendTestMessage: (channelId: string, message?: string) => Promise<void>;
  selectChannel: (channel: Channel | null) => void;
}

export const useNotificationsStore = create<NotificationsState>((set) => ({
  channels: [],
  providers: [],
  selectedChannel: null,
  loading: false,
  error: null,

  fetchChannels: async () => {
    set({ loading: true, error: null });
    try {
      const channels = await api.notifications.listChannels();
      set({ channels, loading: false });
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to fetch channels',
        loading: false,
      });
    }
  },

  fetchProviders: async () => {
    try {
      const providers = await api.notifications.listProviders();
      set({ providers });
    } catch (e) {
      console.error('Failed to fetch providers:', e);
    }
  },

  fetchChannel: async (channelId: string) => {
    set({ loading: true, error: null });
    try {
      const channel = await api.notifications.getChannel(channelId);
      set({ selectedChannel: channel, loading: false });
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to fetch channel',
        loading: false,
      });
    }
  },

  createChannel: async (data: ChannelCreate) => {
    set({ loading: true, error: null });
    try {
      const channel = await api.notifications.createChannel(data);
      set((state) => ({
        channels: [...state.channels, channel],
        loading: false,
      }));
      return channel;
    } catch (e) {
      const error = e instanceof Error ? e.message : 'Failed to create channel';
      set({ error, loading: false });
      throw e;
    }
  },

  updateChannel: async (channelId: string, data: ChannelUpdate) => {
    set({ loading: true, error: null });
    try {
      const channel = await api.notifications.updateChannel(channelId, data);
      set((state) => ({
        channels: state.channels.map((c) => (c.id === channelId ? channel : c)),
        selectedChannel:
          state.selectedChannel?.id === channelId ? channel : state.selectedChannel,
        loading: false,
      }));
      return channel;
    } catch (e) {
      const error = e instanceof Error ? e.message : 'Failed to update channel';
      set({ error, loading: false });
      throw e;
    }
  },

  deleteChannel: async (channelId: string) => {
    set({ loading: true, error: null });
    try {
      await api.notifications.deleteChannel(channelId);
      set((state) => ({
        channels: state.channels.filter((c) => c.id !== channelId),
        selectedChannel:
          state.selectedChannel?.id === channelId ? null : state.selectedChannel,
        loading: false,
      }));
    } catch (e) {
      const error = e instanceof Error ? e.message : 'Failed to delete channel';
      set({ error, loading: false });
      throw e;
    }
  },

  enableChannel: async (channelId: string) => {
    try {
      await api.notifications.enableChannel(channelId);
      set((state) => ({
        channels: state.channels.map((c) =>
          c.id === channelId ? { ...c, enabled: true } : c
        ),
        selectedChannel:
          state.selectedChannel?.id === channelId
            ? { ...state.selectedChannel, enabled: true }
            : state.selectedChannel,
      }));
    } catch (e) {
      throw e;
    }
  },

  disableChannel: async (channelId: string) => {
    try {
      await api.notifications.disableChannel(channelId);
      set((state) => ({
        channels: state.channels.map((c) =>
          c.id === channelId ? { ...c, enabled: false } : c
        ),
        selectedChannel:
          state.selectedChannel?.id === channelId
            ? { ...state.selectedChannel, enabled: false }
            : state.selectedChannel,
      }));
    } catch (e) {
      throw e;
    }
  },

  testChannel: async (channelId: string) => {
    return await api.notifications.testChannel(channelId);
  },

  sendTestMessage: async (channelId: string, message?: string) => {
    await api.notifications.sendTestMessage(channelId, message);
  },

  selectChannel: (channel: Channel | null) => {
    set({ selectedChannel: channel });
  },
}));
