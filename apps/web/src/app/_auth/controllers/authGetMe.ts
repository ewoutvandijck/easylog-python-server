import { protectedProcedure } from '@/lib/trpc/procedures';

const authGetMe = protectedProcedure.query(async ({ ctx }) => {
  return ctx.user;
});

export default authGetMe;
