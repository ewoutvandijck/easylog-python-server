import { useLocale } from 'next-intl';

import { formatDistanceToNow } from '../utils/formatDistanceToNow';

const useRelativeTime = (date: Date) => {
  const locale = useLocale();
  return formatDistanceToNow(date, locale);
};

export default useRelativeTime;
