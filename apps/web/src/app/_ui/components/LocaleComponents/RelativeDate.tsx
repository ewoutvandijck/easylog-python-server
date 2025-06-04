'use client';

import useRelativeTime from '../../hooks/useRelativeTime';

export interface RelativeDateProps extends Intl.DateTimeFormatOptions {
  date: Date;
}

const RelativeDate = ({ date }: RelativeDateProps) => {
  const relativeTime = useRelativeTime(date);
  return relativeTime;
};

export default RelativeDate;
