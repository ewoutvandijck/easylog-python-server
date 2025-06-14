import { z } from 'zod';

import decrypt from '@/lib/security/decrypt';

export interface DecryptZodOptions<T extends z.ZodSchema> {
  encrypted: string;
  decryptionKey: string;
  schema: T;
}

const decryptZod = <T extends z.ZodSchema>({
  encrypted,
  decryptionKey,
  schema
}: DecryptZodOptions<T>): z.infer<T> => {
  const decrypted = decrypt(encrypted, decryptionKey);
  return schema.parse(JSON.parse(decrypted));
};

export default decryptZod;
