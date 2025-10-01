'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Hymn } from '@/types/hymn';

interface BubbleData {
  hymn: Hymn;
  x: number;
  y: number;
  radius: number;
}

export default function HymnBubbles() {
  const [bubbles, setBubbles] = useState<BubbleData[]>([]);
  const [selectedHymn, setSelectedHymn] = useState<Hymn | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function FetchHymns() {
      try {
        const response = await fetch('/api/hymns');
        const hymns: Hymn[] = await response.json();
        
        const bubbleData = hymns.map((hymn, index) => {
          const angle = (index / hymns.length) * 2 * Math.PI;
          const distance = 200 + Math.random() * 300;
          
          return {
            hymn,
            x: Math.cos(angle) * distance,
            y: Math.sin(angle) * distance,
            radius: Math.max(20, Math.min(60, hymn.hymn_score * 5))
          };
        });
        
        setBubbles(bubbleData);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch hymns:', error);
        setLoading(false);
      }
    }
    
    FetchHymns();
  }, []);

  const HandleBubbleClick = (hymn: Hymn) => {
    setSelectedHymn(hymn);
  };

  const HandleCloseDetail = () => {
    setSelectedHymn(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900">
        <div className="text-white text-2xl">Loading Rigveda...</div>
      </div>
    );
  }

  return (
    <div className="relative w-screen h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 overflow-hidden">
      <div className="absolute top-8 left-8 text-white z-10">
        <h1 className="text-4xl font-bold mb-2">Rigveda Explorer</h1>
        <p className="text-lg opacity-80">{bubbles.length} hymns from the ancient texts</p>
      </div>

      <svg className="w-full h-full">
        <g transform={`translate(${typeof window !== 'undefined' ? window.innerWidth / 2 : 800}, ${typeof window !== 'undefined' ? window.innerHeight / 2 : 400})`}>
          {bubbles.map((bubble, index) => (
            <motion.g
              key={bubble.hymn.hymn_id}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.01, duration: 0.5 }}
            >
              <motion.circle
                cx={bubble.x}
                cy={bubble.y}
                r={bubble.radius}
                fill={`hsl(${(bubble.hymn.book_number * 36) % 360}, 70%, 60%)`}
                opacity={0.7}
                className="cursor-pointer"
                onClick={() => HandleBubbleClick(bubble.hymn)}
                whileHover={{ scale: 1.2, opacity: 1 }}
                transition={{ duration: 0.2 }}
              />
              <text
                x={bubble.x}
                y={bubble.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="white"
                fontSize={bubble.radius / 3}
                className="pointer-events-none font-bold"
              >
                {bubble.hymn.book_number}.{bubble.hymn.hymn_number}
              </text>
            </motion.g>
          ))}
        </g>
      </svg>

      <AnimatePresence>
        {selectedHymn && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-20"
            onClick={HandleCloseDetail}
          >
            <motion.div
              initial={{ scale: 0.9, y: 50 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 50 }}
              className="bg-white rounded-lg p-8 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-3xl font-bold text-gray-800 mb-2">
                    Book {selectedHymn.book_number}, Hymn {selectedHymn.hymn_number}
                  </h2>
                  <p className="text-xl text-gray-600">{selectedHymn.title}</p>
                </div>
                <button
                  onClick={HandleCloseDetail}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-700">Deities</h3>
                  <p className="text-gray-600">{selectedHymn.deity_names}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-700">Deity Count</h3>
                    <p className="text-2xl text-purple-600">{selectedHymn.deity_count}</p>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold text-gray-700">Hymn Score</h3>
                    <p className="text-2xl text-purple-600">{selectedHymn.hymn_score.toFixed(2)}</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


