import { useState, useEffect } from "react";

interface LazyImageProps {
  src: string;
  alt: string;
  className?: string;
  placeholder?: string;
  onLoad?: () => void;
  onError?: () => void;
}

export default function LazyImage({
  src,
  alt,
  className = "",
  placeholder = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E",
  onLoad,
  onError,
}: LazyImageProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    const img = new Image();
    img.src = src;
    img.onload = () => {
      setIsLoaded(true);
      onLoad?.();
    };
    img.onerror = () => {
      setHasError(true);
      onError?.();
    };
  }, [src, onLoad, onError]);

  if (hasError) {
    return (
      <div className={`image-placeholder ${className}`}>
        <span>⚠️</span>
      </div>
    );
  }

  return (
    <div className={`lazy-image-wrapper ${className}`}>
      {!isLoaded && <div className="image-skeleton"></div>}
      <img
        src={isLoaded ? src : placeholder}
        alt={alt}
        style={{ opacity: isLoaded ? 1 : 0 }}
        className="lazy-image"
        onLoad={() => setIsLoaded(true)}
      />
    </div>
  );
}
