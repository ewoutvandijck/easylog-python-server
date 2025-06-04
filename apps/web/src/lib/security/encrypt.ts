import crypto from 'crypto';

import encryptionConfig from '@/lib/security/config';

const encrypt = (text: string, encryptionKey: string) => {
  const iv = crypto.randomBytes(encryptionConfig.ivLength);
  const cipher = crypto.createCipheriv(
    encryptionConfig.algorithm,
    Buffer.from(encryptionKey, 'hex'),
    iv,
    {
      authTagLength: encryptionConfig.authTagLength
    }
  );

  let encrypted = cipher.update(text, 'utf8');
  encrypted = Buffer.concat([encrypted, cipher.final()]);
  const authTag = cipher.getAuthTag();

  const buffer = Buffer.concat([iv, authTag, encrypted]);
  return buffer.toString('base64');
};

export default encrypt;
