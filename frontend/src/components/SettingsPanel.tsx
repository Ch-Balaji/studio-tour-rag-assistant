/**
 * Settings Panel Component for RAG Parameters
 */

'use client';

import { ChatSettings } from '@/types';
import { motion, AnimatePresence } from 'framer-motion';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  settings: ChatSettings;
  onSettingsChange: (settings: ChatSettings) => void;
}

export default function SettingsPanel({
  isOpen,
  onClose,
  settings,
  onSettingsChange,
}: SettingsPanelProps) {
  const updateSetting = <K extends keyof ChatSettings>(
    key: K,
    value: ChatSettings[K]
  ) => {
    onSettingsChange({ ...settings, [key]: value });
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          {/* Settings Panel */}
          <motion.div
            initial={{ x: 300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 300, opacity: 0 }}
            transition={{ type: 'spring', damping: 25 }}
            className="fixed right-0 top-0 h-full w-80 bg-card/95 backdrop-blur-md shadow-2xl z-50 overflow-y-auto border-l border-primary/30"
          >
            <div className="p-6">
              {/* Header */}
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-foreground magical-text">⚙️ Settings</h2>
                <motion.button
                  onClick={onClose}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="p-2 hover:bg-primary/10 hover:text-primary rounded-lg transition-colors"
                >
                  <svg
                    className="w-5 h-5 text-foreground"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </motion.button>
              </div>

              {/* Retrieval Settings */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-foreground mb-3">
                  🔍 Retrieval Settings
                </h3>

                {/* Reranking Toggle */}
                <div className="mb-4">
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-foreground-muted">
                      Enable Reranking
                    </span>
                    <input
                      type="checkbox"
                      checked={settings.use_reranking}
                      onChange={(e) =>
                        updateSetting('use_reranking', e.target.checked)
                      }
                      className="w-4 h-4 rounded accent-primary"
                    />
                  </label>
                  <p className="text-xs text-foreground-muted mt-1 opacity-80">
                    Use cross-encoder to rerank results
                  </p>
                </div>

                {/* Initial Top-k */}
                <div className="mb-4">
                  <label className="block text-sm text-foreground-muted mb-2">
                    Initial Retrieval (top-k): <span className="text-primary font-semibold">{settings.initial_top_k}</span>
                  </label>
                  <input
                    type="range"
                    min="5"
                    max="50"
                    step="5"
                    value={settings.initial_top_k}
                    onChange={(e) =>
                      updateSetting('initial_top_k', parseInt(e.target.value))
                    }
                    className="w-full accent-primary"
                  />
                  <p className="text-xs text-foreground-muted mt-1 opacity-80">
                    Number of candidates to retrieve initially
                  </p>
                </div>

                {/* Final Top-n */}
                <div className="mb-4">
                  <label className="block text-sm text-foreground-muted mb-2">
                    Final Results (top-n): <span className="text-primary font-semibold">{settings.final_top_n}</span>
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    step="1"
                    value={settings.final_top_n}
                    onChange={(e) =>
                      updateSetting('final_top_n', parseInt(e.target.value))
                    }
                    className="w-full accent-primary"
                  />
                  <p className="text-xs text-foreground-muted mt-1 opacity-80">
                    Number of final results after reranking
                  </p>
                </div>

                {/* Similarity Threshold */}
                <div className="mb-4">
                  <label className="block text-sm text-foreground-muted mb-2">
                    Similarity Threshold: <span className="text-primary font-semibold">{settings.similarity_threshold.toFixed(2)}</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={settings.similarity_threshold}
                    onChange={(e) =>
                      updateSetting('similarity_threshold', parseFloat(e.target.value))
                    }
                    className="w-full accent-primary"
                  />
                  <p className="text-xs text-foreground-muted mt-1 opacity-80">
                    Minimum similarity score to include results
                  </p>
                </div>
              </div>

              {/* Hybrid Search Settings */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-foreground mb-3">
                  🔀 Hybrid Search
                </h3>

                {/* Hybrid Search Toggle */}
                <div className="mb-4">
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-foreground-muted">
                      Enable Hybrid Search
                    </span>
                    <input
                      type="checkbox"
                      checked={settings.use_hybrid_search}
                      onChange={(e) =>
                        updateSetting('use_hybrid_search', e.target.checked)
                      }
                      className="w-4 h-4 rounded accent-primary"
                    />
                  </label>
                  <p className="text-xs text-foreground-muted mt-1 opacity-80">
                    Combine dense (semantic) and sparse (keyword) search
                  </p>
                </div>

                {/* Hybrid Alpha */}
                <div className="mb-4">
                  <label className="block text-sm text-foreground-muted mb-2">
                    Dense Weight (α): <span className="text-primary font-semibold">{settings.hybrid_alpha.toFixed(2)}</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={settings.hybrid_alpha}
                    onChange={(e) =>
                      updateSetting('hybrid_alpha', parseFloat(e.target.value))
                    }
                    className="w-full accent-primary"
                  />
                  <p className="text-xs text-foreground-muted mt-1 opacity-80">
                    0 = pure keyword, 1 = pure semantic
                  </p>
                </div>

                {/* Query Enhancement Toggle */}
                <div className="mb-4">
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-foreground-muted">
                      Query Enhancement
                    </span>
                    <input
                      type="checkbox"
                      checked={settings.use_query_enhancement}
                      onChange={(e) =>
                        updateSetting('use_query_enhancement', e.target.checked)
                      }
                      className="w-4 h-4 rounded accent-primary"
                    />
                  </label>
                  <p className="text-xs text-foreground-muted mt-1 opacity-80">
                    Expand queries with character variations
                  </p>
                </div>
              </div>

              {/* Citation Settings */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-foreground mb-3">
                  📝 Citation Style
                </h3>

                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="clean"
                      checked={settings.citation_style === 'clean'}
                      onChange={(e) =>
                        updateSetting('citation_style', e.target.value as 'clean' | 'none')
                      }
                      className="mr-2 accent-primary"
                    />
                    <span className="text-sm text-foreground-muted">
                      Clean (numbered footnotes)
                    </span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="none"
                      checked={settings.citation_style === 'none'}
                      onChange={(e) =>
                        updateSetting('citation_style', e.target.value as 'clean' | 'none')
                      }
                      className="mr-2 accent-primary"
                    />
                    <span className="text-sm text-foreground-muted">
                      No citations
                    </span>
                  </label>
                </div>
              </div>

              {/* Reset Button */}
              <motion.button
                onClick={() => {
                  onSettingsChange({
                    use_reranking: true,
                    initial_top_k: 25,
                    final_top_n: 5,
                    similarity_threshold: 0.3,
                    use_hybrid_search: true,
                    hybrid_alpha: 0.5,
                    use_query_enhancement: true,
                    citation_style: 'clean',
                  });
                }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full py-3 px-4 bg-secondary hover:bg-card-hover border border-border hover:border-primary/50 rounded-lg text-foreground text-sm transition-smooth"
              >
                Reset to Defaults
              </motion.button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

