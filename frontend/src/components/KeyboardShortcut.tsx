interface KeyboardShortcutProps {
  keys: string[];
  label?: string;
}

export default function KeyboardShortcut({
  keys,
  label,
}: KeyboardShortcutProps) {
  return (
    <span className="keyboard-shortcut" title={label}>
      {keys.map((key, index) => (
        <kbd key={index} className="kbd">
          {key}
        </kbd>
      ))}
    </span>
  );
}
