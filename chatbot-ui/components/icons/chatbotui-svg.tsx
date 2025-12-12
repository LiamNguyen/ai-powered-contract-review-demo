import { FC } from "react"

interface ChatbotUISVGProps {
  theme: "dark" | "light"
  scale?: number
}

export const ChatbotUISVG: FC<ChatbotUISVGProps> = ({ theme, scale = 1 }) => {
  return (
    <svg
      width={120 * scale}
      height={120 * scale}
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Light bulb icon */}
      <g transform="translate(10, 10)">
        {/* Bulb */}
        <path
          d="M50 10 C30 10, 20 25, 20 40 C20 50, 25 55, 25 65 L35 65 L35 75 C35 80, 40 85, 50 85 C60 85, 65 80, 65 75 L65 65 L75 65 C75 55, 80 50, 80 40 C80 25, 70 10, 50 10 Z"
          fill={`${theme === "dark" ? "#FCD34D" : "#F59E0B"}`}
          stroke={`${theme === "dark" ? "#fff" : "#000"}`}
          strokeWidth="3"
        />
        {/* Filament */}
        <path
          d="M45 25 L45 45 M50 20 L50 45 M55 25 L55 45"
          stroke={`${theme === "dark" ? "#92400E" : "#78350F"}`}
          strokeWidth="2"
          strokeLinecap="round"
        />
        {/* Base */}
        <rect
          x="42"
          y="85"
          width="16"
          height="8"
          rx="2"
          fill={`${theme === "dark" ? "#fff" : "#000"}`}
        />
        {/* Light rays */}
        <g stroke={`${theme === "dark" ? "#FCD34D" : "#F59E0B"}`} strokeWidth="3" strokeLinecap="round">
          <line x1="10" y1="40" x2="5" y2="40" />
          <line x1="90" y1="40" x2="95" y2="40" />
          <line x1="20" y1="15" x2="15" y2="10" />
          <line x1="80" y1="15" x2="85" y2="10" />
          <line x1="20" y1="65" x2="15" y2="70" />
          <line x1="80" y1="65" x2="85" y2="70" />
        </g>
      </g>
    </svg>
  )
}
