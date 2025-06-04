import crypto from 'crypto';

import encryptionConfig from '@/lib/security/config';

const decrypt = (encryptedText: string, encryptionKey: string) => {
  const buffer = Buffer.from(encryptedText, 'base64');

  const iv = buffer.subarray(0, encryptionConfig.ivLength);
  const authTag = buffer.subarray(
    encryptionConfig.ivLength,
    encryptionConfig.ivLength + encryptionConfig.authTagLength
  );

  const ciphertext = buffer.subarray(
    encryptionConfig.ivLength + encryptionConfig.authTagLength
  );

  const decipher = crypto.createDecipheriv(
    encryptionConfig.algorithm,
    Buffer.from(encryptionKey, 'hex'),
    iv
  );

  decipher.setAuthTag(authTag);

  let decrypted = decipher.update(ciphertext);
  decrypted = Buffer.concat([decrypted, decipher.final()]);

  return decrypted.toString('utf8');
};

export default decrypt;
