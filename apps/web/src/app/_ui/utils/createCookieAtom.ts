import { deleteCookie, setCookie } from 'cookies-next';
import { getCookie } from 'cookies-next/client';
import { atomWithStorage } from 'jotai/utils';
import { z } from 'zod';

/**
 * Creates an atom that stores its value in a cookie with Zod validation
 *
 * @param cookieName The name of the cookie
 * @param schema The Zod schema for validating cookie data
 * @param initialValue The initial value of the atom
 * @param expirationTimeSeconds How long the cookie should last in seconds
 * @returns A Jotai atom that reads/writes to a cookie with validation
 */
const createCookieAtom = <T extends z.ZodType>(
  cookieName: string,
  schema: T,
  initialValue: z.infer<T>,
  expirationTimeSeconds = 365 * 24 * 60 * 60
) => {
  return atomWithStorage<z.infer<T>>(cookieName, initialValue, {
    setItem(key, newValue) {
      void setCookie(key, JSON.stringify(newValue), {
        expires: new Date(Date.now() + expirationTimeSeconds * 1000)
      });
    },
    getItem(key) {
      const cookie = getCookie(key);
      if (!cookie) return initialValue;

      try {
        const result = schema.safeParse(cookie as string);

        if (result.success) {
          return result.data;
        } else {
          console.warn(`Invalid cookie data for ${key}:`, result.error);
          return initialValue;
        }
      } catch (e) {
        console.warn(`Error parsing cookie ${key}:`, e);
        return initialValue;
      }
    },
    removeItem(key) {
      void deleteCookie(key);
    }
  });
};

export default createCookieAtom;
