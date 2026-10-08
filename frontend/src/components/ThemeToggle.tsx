import { useTheme } from "../hooks/useTheme";

const ICON = { system: "🖥", light: "☀", dark: "☾" } as const;
const LABEL = { system: "System theme", light: "Light theme", dark: "Dark theme" } as const;

export function ThemeToggle() {
  const { theme, cycleTheme } = useTheme();

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={cycleTheme}
      title={`${LABEL[theme]} (click to change)`}
      aria-label={`${LABEL[theme]}, click to change`}
    >
      {ICON[theme]}
    </button>
  );
}
