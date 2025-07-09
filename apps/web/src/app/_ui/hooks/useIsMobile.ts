import { useEffect, useState } from 'react';

const MOBILE_BREAKPOINT = 768;

const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState<boolean | undefined>(undefined);

  useEffect(() => {
    const controller = new AbortController();

    const mediaQueryList = window.matchMedia(
      `(max-width: ${MOBILE_BREAKPOINT - 1}px)`
    );

    mediaQueryList.addEventListener(
      'change',
      () => {
        setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
      },
      {
        signal: controller.signal
      }
    );

    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);

    return () => {
      controller.abort();
    };
  }, []);

  return !!isMobile;
};

export default useIsMobile;
