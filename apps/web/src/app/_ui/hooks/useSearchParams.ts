import { useEffect, useState } from 'react';

const useSearchParams = () => {
  const [searchParams, setSearchParams] = useState<URLSearchParams>(
    new URLSearchParams()
  );

  useEffect(() => {
    if (window.location.search) {
      setSearchParams(new URLSearchParams(window.location.search));
    }
  }, []);

  return searchParams;
};

export default useSearchParams;
