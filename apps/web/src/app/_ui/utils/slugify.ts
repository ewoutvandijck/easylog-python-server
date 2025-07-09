/**
 * Generate a slug from a string
 *
 * @param text The string to generate a slug from
 * @returns The slug
 * @see https://byby.dev/js-slugify-string
 */
const slugify = (text: string) => {
  return (
    String(text)
      /**
       * Split accented characters into their base characters and diacritical
       * marks.
       *
       * @see https://en.wikipedia.org/wiki/Diacritic
       */
      .normalize('NFKD')
      /**
       * Remove all the accents, which happen to be all in the \u03xx UNICODE
       * block.
       */
      .replace(/[\u0300-\u036f]/g, '')
      /** Trim leading or trailing whitespace. */
      .trim()
      /** Convert to lowercase. */
      .toLowerCase()
      /** Remove non-alphanumeric characters. */
      .replace(/[^a-z0-9 -]/g, '')
      /** Replace spaces with hyphens. */
      .replace(/\s+/g, '-')
      /** Remove consecutive hyphens. */
      .replace(/-+/g, '-')
  );
};

export default slugify;
