import crypto from 'crypto';

export function verifyPassword(plainPassword: string, hashedPassword: string): boolean {
  if (!hashedPassword || !hashedPassword.includes(':')) {
    return false;
  }

  const [salt, storedHash] = hashedPassword.split(':');
  const computedHash = crypto.createHash('sha256').update(salt + plainPassword).digest('hex');

  return crypto.timingSafeEqual(Buffer.from(computedHash), Buffer.from(storedHash));
}

export function getPasswordHash(password: string): string {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.createHash('sha256').update(salt + password).digest('hex');
  return `${salt}:${hash}`;
}
