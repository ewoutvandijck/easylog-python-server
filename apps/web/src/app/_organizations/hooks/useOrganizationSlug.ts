import { useParams } from 'next/navigation';
import { z } from 'zod';

const useOrganizationSlug = <T extends boolean = true>(throwOnInvalid?: T) => {
  const params = useParams();

  const result = z
    .object({
      organizationSlug: z.string()
    })
    .safeParse(params);

  if (!result.success && throwOnInvalid) {
    throw new Error('Invalid params');
  }

  const organizationSlug = result.data?.organizationSlug ?? null;

  return organizationSlug as T extends true ? string : string | null;
};

export default useOrganizationSlug;
