import { useRef, useEffect, forwardRef, useImperativeHandle } from 'react';

interface Props {
  src: string;
  onReady?: () => void;
}

export interface VideoPlayerHandle {
  getVideoElement: () => HTMLVideoElement | null;
}

const VideoPlayer = forwardRef<VideoPlayerHandle, Props>(({ src, onReady }, ref) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useImperativeHandle(ref, () => ({
    getVideoElement: () => videoRef.current,
  }));

  useEffect(() => {
    if (src && videoRef.current) {
      videoRef.current.load();
    }
  }, [src]);

  return (
    <div className="video-container">
      <video
        ref={videoRef}
        controls
        crossOrigin="anonymous"
        onCanPlay={onReady}
        style={{ width: '100%', maxHeight: '400px', borderRadius: '8px' }}
      >
        <source src={src} type="video/mp4" />
        Your browser does not support the video element.
      </video>
    </div>
  );
});

VideoPlayer.displayName = 'VideoPlayer';
export default VideoPlayer;
