const encryptionConfig = {
  algorithm: 'aes-256-gcm',
  ivLength: 12,
  authTagLength: 16
} as const;

export default encryptionConfig;
