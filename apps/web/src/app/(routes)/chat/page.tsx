import { headers } from 'next/headers';
import { forbidden } from 'next/navigation';

import getCurrentUser from '@/app/_auth/data/getCurrentUser';
import Typography from '@/app/_ui/components/Typography/Typography';

const ChatPage = async () => {
  const user = await getCurrentUser(await headers());

  if (!user) {
    throw forbidden();
  }

  return (
    <div className="p-10">
      <Typography variant="labelMd">{user.name}</Typography>
      <Typography variant="bodySm" colorRole="muted">
        {user.email}
      </Typography>
    </div>
  );
};

export default ChatPage;
