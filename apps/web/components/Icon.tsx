import type { CSSProperties } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Award,
  Bell,
  BookOpen,
  Calendar,
  ChartColumn,
  Check,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  CircleQuestionMark,
  Clock,
  Download,
  Ear,
  ExternalLink,
  Eye,
  EyeOff,
  Flag,
  Flame,
  Globe,
  Hand,
  Headphones,
  House,
  Info,
  Keyboard,
  Languages,
  Layers,
  Lightbulb,
  List,
  Menu,
  MessageCircle,
  Mic,
  Pause,
  PenLine,
  Play,
  Plus,
  RefreshCw,
  Repeat,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Star,
  Target,
  Timer,
  Trash,
  TriangleAlert,
  Trophy,
  User,
  Volume2,
  X,
  Zap,
  type LucideIcon,
} from "lucide-react";

/** The icon vocabulary of the app. Names stay stable; the glyphs come from lucide-react. */
const icons = {
  home: House,
  book: BookOpen,
  headphones: Headphones,
  mic: Mic,
  pen: PenLine,
  chart: ChartColumn,
  settings: SlidersHorizontal,
  arrow: ArrowRight,
  "arrow-left": ArrowLeft,
  check: Check,
  chevron: ChevronRight,
  "chevron-down": ChevronDown,
  "chevron-up": ChevronUp,
  globe: Globe,
  shield: ShieldCheck,
  clock: Clock,
  download: Download,
  user: User,
  calendar: Calendar,
  help: CircleQuestionMark,
  close: X,
  volume: Volume2,
  play: Play,
  pause: Pause,
  info: Info,
  alert: TriangleAlert,
  sparkles: Sparkles,
  flame: Flame,
  trophy: Trophy,
  star: Star,
  search: Search,
  refresh: RefreshCw,
  trash: Trash,
  plus: Plus,
  menu: Menu,
  eye: Eye,
  "eye-off": EyeOff,
  flag: Flag,
  message: MessageCircle,
  languages: Languages,
  lightbulb: Lightbulb,
  target: Target,
  award: Award,
  external: ExternalLink,
  layers: Layers,
  list: List,
  bell: Bell,
  repeat: Repeat,
  timer: Timer,
  zap: Zap,
  hand: Hand,
  keyboard: Keyboard,
  ear: Ear,
} satisfies Record<string, LucideIcon>;

export type IconName = keyof typeof icons;

export const ICON_NAMES = Object.keys(icons) as IconName[];

export function Icon({
  name,
  size = 20,
  className = "",
  style,
}: {
  name: IconName;
  size?: number;
  className?: string;
  style?: CSSProperties;
}) {
  const Glyph = icons[name];
  return (
    <Glyph
      className={`icon ${className}`.trim()}
      size={size}
      strokeWidth={1.75}
      aria-hidden="true"
      focusable="false"
      style={style}
    />
  );
}
