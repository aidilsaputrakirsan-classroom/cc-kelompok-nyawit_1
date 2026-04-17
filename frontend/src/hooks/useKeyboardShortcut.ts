import { useEffect } from "react";

type KeyCombination = {
  key: string;
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
};

type ShortcutHandler = (event: KeyboardEvent) => void;

interface UseKeyboardShortcutOptions {
  combination: KeyCombination;
  handler: ShortcutHandler;
  enabled?: boolean;
  preventDefault?: boolean;
}

/**
 * Custom hook for keyboard shortcuts
 * @example
 * // Ctrl+S to save
 * useKeyboardShortcut({
 *   combination: { key: 's', ctrl: true },
 *   handler: () => handleSave(),
 * });
 */
export default function useKeyboardShortcut({
  combination,
  handler,
  enabled = true,
  preventDefault = true,
}: UseKeyboardShortcutOptions) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      const { key, ctrlKey, altKey, shiftKey } = event;
      const {
        key: targetKey,
        ctrl = false,
        alt = false,
        shift = false,
      } = combination;

      // Check if all modifiers match
      const matchesModifiers =
        ctrlKey === ctrl && altKey === alt && shiftKey === shift;

      // Check if the key matches (case-insensitive)
      const matchesKey = key.toLowerCase() === targetKey.toLowerCase();

      if (matchesModifiers && matchesKey) {
        if (preventDefault) {
          event.preventDefault();
        }
        handler(event);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [combination, handler, enabled, preventDefault]);
}
