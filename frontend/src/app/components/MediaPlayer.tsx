import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Slider } from '@/app/components/ui/slider';
import { Input } from '@/app/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/app/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/app/components/ui/select';
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  Download,
  Share2,
  Scissors,
  Copy,
  Clock,
  Settings,
  FastForward,
  Rewind,
  SkipForward,
  SkipBack,
  Volume1,
} from 'lucide-react';
import { cn, formatDuration } from '@/app/components/ui/utils';
import { toast } from 'sonner';

interface MediaPlayerProps {
  src: string;
  type: 'audio' | 'video';
  title: string;
  poster?: string;
  onClipExport?: (startTime: number, endTime: number) => void;
}

export function MediaPlayer({ src, type, title, poster, onClipExport }: MediaPlayerProps) {
  const mediaRef = useRef<HTMLVideoElement | HTMLAudioElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  
  // Clipping state
  const [isClipping, setIsClipping] = useState(false);
  const [clipStart, setClipStart] = useState<number | null>(null);
  const [clipEnd, setClipEnd] = useState<number | null>(null);
  const [showExportModal, setShowExportModal] = useState(false);
  
  // Share state
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareUrl, setShareUrl] = useState('');
  const [shareExpiry, setShareExpiry] = useState('7');

  useEffect(() => {
    const media = mediaRef.current;
    if (!media) return;

    const handleTimeUpdate = () => setCurrentTime(media.currentTime);
    const handleLoadedMetadata = () => setDuration(media.duration);
    const handleEnded = () => setIsPlaying(false);

    media.addEventListener('timeupdate', handleTimeUpdate);
    media.addEventListener('loadedmetadata', handleLoadedMetadata);
    media.addEventListener('ended', handleEnded);

    return () => {
      media.removeEventListener('timeupdate', handleTimeUpdate);
      media.removeEventListener('loadedmetadata', handleLoadedMetadata);
      media.removeEventListener('ended', handleEnded);
    };
  }, []);

  const togglePlay = useCallback(() => {
    const media = mediaRef.current;
    if (!media) return;

    if (isPlaying) {
      media.pause();
    } else {
      media.play();
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const handleSeek = useCallback((value: number[]) => {
    const media = mediaRef.current;
    if (!media) return;
    media.currentTime = value[0];
    setCurrentTime(value[0]);
  }, []);

  const handleVolumeChange = useCallback((value: number[]) => {
    const media = mediaRef.current;
    if (!media) return;
    media.volume = value[0];
    setVolume(value[0]);
    setIsMuted(value[0] === 0);
  }, []);

  const toggleMute = useCallback(() => {
    const media = mediaRef.current;
    if (!media) return;
    media.muted = !isMuted;
    setIsMuted(!isMuted);
  }, [isMuted]);

  const toggleFullscreen = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;

    if (!isFullscreen) {
      container.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
    setIsFullscreen(!isFullscreen);
  }, [isFullscreen]);

  const handlePlaybackRateChange = useCallback((rate: number) => {
    const media = mediaRef.current;
    if (!media) return;
    media.playbackRate = rate;
    setPlaybackRate(rate);
    setShowSettings(false);
  }, []);

  const skip = useCallback((seconds: number) => {
    const media = mediaRef.current;
    if (!media) return;
    media.currentTime = Math.max(0, Math.min(duration, media.currentTime + seconds));
  }, [duration]);

  const setClipStartTime = useCallback(() => {
    setClipStart(currentTime);
    setIsClipping(true);
    toast.info('Clip start set. Set end time to complete.');
  }, [currentTime]);

  const setClipEndTime = useCallback(() => {
    if (clipStart !== null && currentTime > clipStart) {
      setClipEnd(currentTime);
      setShowExportModal(true);
      setIsClipping(false);
    } else {
      toast.error('End time must be after start time');
    }
  }, [clipStart, currentTime]);

  const cancelClip = useCallback(() => {
    setClipStart(null);
    setClipEnd(null);
    setIsClipping(false);
  }, []);

  const handleExportClip = useCallback(() => {
    if (clipStart !== null && clipEnd !== null && onClipExport) {
      onClipExport(clipStart, clipEnd);
      setShowExportModal(false);
      setClipStart(null);
      setClipEnd(null);
      toast.success('Clip export started');
    }
  }, [clipStart, clipEnd, onClipExport]);

  const generateShareLink = useCallback(() => {
    const expiryDate = new Date();
    expiryDate.setDate(expiryDate.getDate() + parseInt(shareExpiry));
    
    // Generate mock share URL
    const shareId = Math.random().toString(36).substring(7);
    const url = `${window.location.origin}/share/${shareId}?expires=${expiryDate.toISOString()}`;
    setShareUrl(url);
    toast.success('Share link generated');
  }, [shareExpiry]);

  const copyShareLink = useCallback(() => {
    navigator.clipboard.writeText(shareUrl);
    toast.success('Link copied to clipboard');
  }, [shareUrl]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <>
      <Card ref={containerRef} className="overflow-hidden">
        <CardContent className="p-0">
          {/* Video/Audio Player */}
          <div 
            className={cn(
              'relative bg-black group',
              type === 'video' ? 'aspect-video' : 'aspect-[2/1]'
            )}
            onMouseEnter={() => setShowControls(true)}
            onMouseLeave={() => setShowControls(false)}
          >
            {type === 'video' ? (
              <video
                ref={mediaRef as React.RefObject<HTMLVideoElement>}
                src={src}
                poster={poster}
                className="w-full h-full object-contain"
                onClick={togglePlay}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800">
                <div className="text-center">
                  <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-blue-600 flex items-center justify-center">
                    {isPlaying ? (
                      <Pause className="w-12 h-12 text-white" />
                    ) : (
                      <Play className="w-12 h-12 text-white ml-1" />
                    )}
                  </div>
                  <p className="text-white font-medium">{title}</p>
                </div>
              </div>
            )}

            {/* Play/Pause Overlay */}
            {!isPlaying && (
              <button
                className="absolute inset-0 flex items-center justify-center bg-black/30"
                onClick={togglePlay}
              >
                <div className="w-20 h-20 rounded-full bg-white/90 flex items-center justify-center hover:bg-white transition-colors">
                  <Play className="w-10 h-10 text-black ml-1" />
                </div>
              </button>
            )}

            {/* Controls */}
            <div className={cn(
              'absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 transition-opacity',
              showControls ? 'opacity-100' : 'opacity-0'
            )}>
              {/* Progress Bar */}
              <div ref={progressRef} className="relative mb-4 cursor-pointer">
                <div className="h-1 bg-white/30 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${(currentTime / duration) * 100}%` }}
                  />
                  {/* Clip range indicator */}
                  {clipStart !== null && clipEnd !== null && (
                    <div 
                      className="absolute top-0 h-full bg-yellow-500/50"
                      style={{ 
                        left: `${(clipStart / duration) * 100}%`,
                        width: `${((clipEnd - clipStart) / duration) * 100}%`
                      }}
                    />
                  )}
                </div>
                <Slider
                  value={[currentTime]}
                  max={duration}
                  step={0.1}
                  onValueChange={handleSeek}
                  className="absolute inset-0 opacity-0"
                />
              </div>

              {/* Control Buttons */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {/* Play/Pause */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-white hover:bg-white/20"
                    onClick={togglePlay}
                  >
                    {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                  </Button>

                  {/* Skip controls */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-white hover:bg-white/20"
                    onClick={() => skip(-10)}
                  >
                    <SkipBack className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-white hover:bg-white/20"
                    onClick={() => skip(10)}
                  >
                    <SkipForward className="w-4 h-4" />
                  </Button>

                  {/* Volume */}
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-white hover:bg-white/20"
                      onClick={toggleMute}
                    >
                      {isMuted || volume === 0 ? (
                        <VolumeX className="w-5 h-5" />
                      ) : (
                        <Volume2 className="w-5 h-5" />
                      )}
                    </Button>
                    <div className="w-20">
                      <Slider
                        value={[isMuted ? 0 : volume]}
                        max={1}
                        step={0.1}
                        onValueChange={handleVolumeChange}
                        className="cursor-pointer"
                      />
                    </div>
                  </div>

                  {/* Time */}
                  <span className="text-white text-sm ml-2">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {/* Clip controls */}
                  {clipStart === null ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-white hover:bg-white/20"
                      onClick={setClipStartTime}
                    >
                      <Scissors className="w-4 h-4 mr-1" />
                      Clip
                    </Button>
                  ) : (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-white hover:bg-white/20"
                      onClick={setClipEndTime}
                    >
                      <Scissors className="w-4 h-4 mr-1" />
                      End Clip
                    </Button>
                  )}

                  {/* Share */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-white hover:bg-white/20"
                    onClick={() => setShowShareModal(true)}
                  >
                    <Share2 className="w-5 h-5" />
                  </Button>

                  {/* Download */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-white hover:bg-white/20"
                    onClick={() => toast.success('Download started')}
                  >
                    <Download className="w-5 h-5" />
                  </Button>

                  {/* Settings */}
                  <div className="relative">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-white hover:bg-white/20"
                      onClick={() => setShowSettings(!showSettings)}
                    >
                      <Settings className="w-5 h-5" />
                    </Button>
                    {showSettings && (
                      <div className="absolute bottom-full right-0 mb-2 bg-gray-900 rounded-lg p-2 min-w-[120px]">
                        <p className="text-xs text-gray-400 mb-2 px-2">Playback Speed</p>
                        {[0.5, 0.75, 1, 1.25, 1.5, 2].map(rate => (
                          <button
                            key={rate}
                            className={cn(
                              'block w-full text-left px-2 py-1 text-sm rounded hover:bg-gray-800',
                              playbackRate === rate ? 'text-blue-400' : 'text-white'
                            )}
                            onClick={() => handlePlaybackRateChange(rate)}
                          >
                            {rate}x
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Fullscreen */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-white hover:bg-white/20"
                    onClick={toggleFullscreen}
                  >
                    {isFullscreen ? (
                      <Minimize className="w-5 h-5" />
                    ) : (
                      <Maximize className="w-5 h-5" />
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Title and Actions */}
          <div className="p-4 bg-gray-50">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium">{title}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="secondary">{type === 'video' ? 'Video' : 'Audio'}</Badge>
                  <span className="text-sm text-gray-500">{formatDuration(duration)}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {clipStart !== null && clipEnd !== null && (
                  <Badge className="bg-yellow-100 text-yellow-700">
                    Clip: {formatTime(clipStart)} - {formatTime(clipEnd)}
                    <button className="ml-1" onClick={cancelClip}>×</button>
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Export Clip Modal */}
      <Dialog open={showExportModal} onOpenChange={setShowExportModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Export Clip</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-500" />
                <span>Clip Duration</span>
              </div>
              <span className="font-mono">
                {clipStart !== null && clipEnd !== null && formatTime(clipEnd - clipStart)}
              </span>
            </div>
            <div>
              <label className="text-sm font-medium">Output Format</label>
              <div className="flex gap-2 mt-2">
                {['MP4', 'MP3', 'WAV'].map(format => (
                  <Button
                    key={format}
                    variant={format === 'MP4' ? 'default' : 'outline'}
                    size="sm"
                  >
                    {format}
                  </Button>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowExportModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleExportClip}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Share Modal */}
      <Dialog open={showShareModal} onOpenChange={setShowShareModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Share File</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium">Share Link</label>
              <div className="flex gap-2 mt-2">
                <Input
                  value={shareUrl || 'Generate a link first'}
                  readOnly
                  className="flex-1"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={shareUrl ? copyShareLink : generateShareLink}
                >
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Link Expiry</label>
              <Select value={shareExpiry} onValueChange={setShareExpiry}>
                <SelectTrigger className="mt-2 w-[200px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 day</SelectItem>
                  <SelectItem value="7">7 days</SelectItem>
                  <SelectItem value="30">30 days</SelectItem>
                  <SelectItem value="0">Never</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="allowDownload" className="rounded" />
              <label htmlFor="allowDownload" className="text-sm">
                Allow recipient to download
              </label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowShareModal(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default MediaPlayer;
