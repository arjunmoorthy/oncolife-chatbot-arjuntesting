export const getUserTimezone = (): string => {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
};

export const formatDateForDisplay = (dateString: string, timezone?: string): string => {
  const date = new Date(dateString);
  const userTz = timezone || getUserTimezone();
  
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    timeZone: userTz
  });
};

export const formatTimeForDisplay = (dateString: string, timezone?: string): string => {
  const date = new Date(dateString);
  const userTz = timezone || getUserTimezone();
  
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: userTz
  });
};

export const getTodayInUserTimezone = (timezone?: string): Date => {
  const userTz = timezone || getUserTimezone();
  const now = new Date();
  const todayInUserTz = new Date(now.toLocaleDateString("en-CA", {timeZone: userTz}));
  return todayInUserTz;
}; 