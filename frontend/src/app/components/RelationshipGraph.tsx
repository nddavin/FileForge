import React, { useState, useCallback, useMemo } from 'react';
import { useFileManager } from '@/contexts/FileManagerContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Input } from '@/app/components/ui/input';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import {
  Search,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Share2,
  FileAudio,
  FileVideo,
  File as FileIcon,
  Link2,
  X,
} from 'lucide-react';
import { cn } from '@/app/components/ui/utils';

interface FileNode {
  id: string;
  name: string;
  type: string;
  series?: string;
  speaker?: string;
  status?: string;
  x: number;
  y: number;
}

interface FileEdge {
  source: string;
  target: string;
  label?: string;
  type: 'series' | 'related' | 'cross-reference';
}

interface RelationshipGraphProps {
  className?: string;
}

// Generate sample relationships based on file metadata
function generateRelationships(files: any[]): { nodes: FileNode[]; edges: FileEdge[] } {
  const nodes: FileNode[] = files.map((file, index) => ({
    id: file.id,
    name: file.name,
    type: file.type,
    series: file.metadata?.series,
    speaker: file.metadata?.speaker,
    status: file.metadata?.status,
    x: 150 + (index % 4) * 200,
    y: 100 + Math.floor(index / 4) * 150,
  }));

  const edges: FileEdge[] = [];
  
  // Generate series relationships
  const seriesMap = new Map<string, string[]>();
  files.forEach((file) => {
    const series = file.metadata?.series;
    if (series) {
      if (!seriesMap.has(series)) {
        seriesMap.set(series, []);
      }
      seriesMap.get(series)!.push(file.id);
    }
  });

  seriesMap.forEach((fileIds) => {
    for (let i = 0; i < fileIds.length - 1; i++) {
      edges.push({
        source: fileIds[i],
        target: fileIds[i + 1],
        label: 'Series',
        type: 'series',
      });
    }
  });

  // Generate cross-references based on same speaker
  const speakerMap = new Map<string, string[]>();
  files.forEach((file) => {
    const speaker = file.metadata?.speaker;
    if (speaker) {
      if (!speakerMap.has(speaker)) {
        speakerMap.set(speaker, []);
      }
      speakerMap.get(speaker)!.push(file.id);
    }
  });

  speakerMap.forEach((fileIds) => {
    if (fileIds.length > 1) {
      for (let i = 0; i < fileIds.length - 1; i++) {
        // Only add if not already connected via series
        const exists = edges.some(
          (e) =>
            (e.source === fileIds[i] && e.target === fileIds[i + 1]) ||
            (e.source === fileIds[i + 1] && e.target === fileIds[i])
        );
        if (!exists) {
          edges.push({
            source: fileIds[i],
            target: fileIds[i + 1],
            label: 'Same Speaker',
            type: 'cross-reference',
          });
        }
      }
    }
  });

  // Add some random related connections for demo
  for (let i = 0; i < Math.min(files.length - 1, 3); i++) {
    edges.push({
      source: files[i].id,
      target: files[i + 1].id,
      label: 'Related',
      type: 'related',
    });
  }

  return { nodes, edges };
}

export function RelationshipGraph({ className }: RelationshipGraphProps) {
  const { files, loading } = useFileManager();
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState<FileNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [hoveredEdge, setHoveredEdge] = useState<FileEdge | null>(null);

  const { nodes, edges } = useMemo(() => {
    if (files.length === 0) {
      return { nodes: [], edges: [] };
    }
    return generateRelationships(files);
  }, [files]);

  const filteredNodes = useMemo(() => {
    if (!searchQuery) return nodes;
    const query = searchQuery.toLowerCase();
    return nodes.filter(
      (node) =>
        node.name.toLowerCase().includes(query) ||
        node.series?.toLowerCase().includes(query) ||
        node.speaker?.toLowerCase().includes(query)
    );
  }, [nodes, searchQuery]);

  const handleZoomIn = useCallback(() => {
    setZoom((prev) => Math.min(prev + 0.2, 2));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom((prev) => Math.max(prev - 0.2, 0.4));
  }, []);

  const handleReset = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, []);

  const getFileIcon = (type: string) => {
    if (type.startsWith('audio/')) return FileAudio;
    if (type.startsWith('video/')) return FileVideo;
    return FileIcon;
  };

  const getEdgeColor = (type: string) => {
    switch (type) {
      case 'series':
        return '#3b82f6';
      case 'cross-reference':
        return '#8b5cf6';
      case 'related':
        return '#10b981';
      default:
        return '#6b7280';
    }
  };

  const getNodePosition = (node: FileNode) => ({
    x: node.x * zoom + pan.x,
    y: node.y * zoom + pan.y,
  });

  if (loading) {
    return (
      <Card className={cn('', className)}>
        <CardContent className="flex items-center justify-center h-96">
          <div className="text-lg text-gray-500">Loading relationships...</div>
        </CardContent>
      </Card>
    );
  }

  if (files.length === 0) {
    return (
      <Card className={cn('', className)}>
        <CardContent className="flex flex-col items-center justify-center h-96">
          <Share2 className="w-16 h-16 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No files to visualize</h3>
          <p className="text-sm text-gray-500">
            Upload files with metadata to see their relationships
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">File Relationships</CardTitle>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 w-48 h-8"
              />
            </div>
            <Button variant="outline" size="icon" onClick={handleZoomOut}>
              <ZoomOut className="w-4 h-4" />
            </Button>
            <span className="text-sm text-gray-500 min-w-[3rem] text-center">
              {Math.round(zoom * 100)}%
            </span>
            <Button variant="outline" size="icon" onClick={handleZoomIn}>
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={handleReset}>
              <Maximize2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
        <div className="flex items-center gap-4 mt-2">
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-blue-500" />
            <span className="text-xs text-gray-500">Series</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-purple-500" />
            <span className="text-xs text-gray-500">Cross-reference</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-green-500" />
            <span className="text-xs text-gray-500">Related</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="relative bg-gray-50 h-[500px] overflow-hidden">
          <svg className="w-full h-full" viewBox="0 0 800 500">
            <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
              {/* Draw edges */}
              {edges.map((edge, index) => {
                const source = nodes.find((n) => n.id === edge.source);
                const target = nodes.find((n) => n.id === edge.target);
                if (!source || !target) return null;

                const isHovered =
                  hoveredEdge?.source === edge.source && hoveredEdge?.target === edge.target;
                const sourcePos = getNodePosition(source);
                const targetPos = getNodePosition(target);
                const midX = (sourcePos.x + targetPos.x) / 2;
                const midY = (sourcePos.y + targetPos.y) / 2;

                return (
                  <g key={`${edge.source}-${edge.target}-${index}`}>
                    <line
                      x1={sourcePos.x + 60}
                      y1={sourcePos.y + 40}
                      x2={targetPos.x + 60}
                      y2={targetPos.y + 40}
                      stroke={getEdgeColor(edge.type)}
                      strokeWidth={isHovered ? 3 : 1.5}
                      strokeOpacity={isHovered ? 1 : 0.5}
                      className="transition-all cursor-pointer"
                      onMouseEnter={() => setHoveredEdge(edge)}
                      onMouseLeave={() => setHoveredEdge(null)}
                    />
                    {isHovered && edge.label && (
                      <g>
                        <rect
                          x={midX - 30}
                          y={midY - 10}
                          width={edge.label.length * 6 + 20}
                          height={20}
                          rx={4}
                          fill="white"
                          stroke={getEdgeColor(edge.type)}
                        />
                        <text
                          x={midX}
                          y={midY + 4}
                          textAnchor="middle"
                          fontSize={11}
                          fill="#374151"
                        >
                          {edge.label}
                        </text>
                      </g>
                    )}
                  </g>
                );
              })}

              {/* Draw nodes */}
              {filteredNodes.map((node) => {
                const Icon = getFileIcon(node.type);
                const pos = getNodePosition(node);
                const isSelected = selectedNode?.id === node.id;

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    className="cursor-pointer transition-all"
                    onClick={() => setSelectedNode(isSelected ? null : node)}
                  >
                    <rect
                      width={120}
                      height={80}
                      rx={8}
                      fill="white"
                      stroke={isSelected ? '#3b82f6' : '#e5e7eb'}
                      strokeWidth={isSelected ? 2 : 1}
                      className="shadow-sm"
                    />
                    <foreignObject width={120} height={80}>
                      <div className="p-3 flex flex-col h-full">
                        <div className="flex items-center gap-2">
                          <Icon className="w-5 h-5 text-blue-500 flex-shrink-0" />
                          <span className="text-xs font-medium truncate flex-1">
                            {node.name}
                          </span>
                        </div>
                        {node.series && (
                          <Badge variant="secondary" className="mt-1 text-[10px] h-5">
                            {node.series}
                          </Badge>
                        )}
                        {node.speaker && (
                          <span className="text-[10px] text-gray-500 mt-1">
                            {node.speaker}
                          </span>
                        )}
                      </div>
                    </foreignObject>
                  </g>
                );
              })}
            </g>
          </svg>

          {/* Selected node details */}
          {selectedNode && (
            <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-4 w-64">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-sm">File Details</h4>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => setSelectedNode(null)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-sm font-medium truncate">{selectedNode.name}</p>
              {selectedNode.series && (
                <p className="text-xs text-gray-500 mt-1">Series: {selectedNode.series}</p>
              )}
              {selectedNode.speaker && (
                <p className="text-xs text-gray-500 mt-1">Speaker: {selectedNode.speaker}</p>
              )}
              <p className="text-xs text-gray-500 mt-1">Status: {selectedNode.status || 'N/A'}</p>
              <div className="flex items-center gap-2 mt-3">
                <Button variant="outline" size="sm" className="text-xs">
                  <Link2 className="w-3 h-3 mr-1" />
                  View File
                </Button>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
