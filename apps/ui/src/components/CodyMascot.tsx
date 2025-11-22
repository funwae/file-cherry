'use client'

import Image from 'next/image'

interface CodyMascotProps {
  size?: 'sm' | 'md' | 'lg'
  mood?: 'idle' | 'loading' | 'working' | 'done'
}

export function CodyMascot({ size = 'md', mood = 'idle' }: CodyMascotProps) {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-16 h-16',
    lg: 'w-24 h-24',
  }

  return (
    <div className={`${sizeClasses[size]} relative flex-shrink-0`}>
      <Image
        src="/mascots/cody.png"
        alt="Cody the Cherry Picker"
        width={size === 'sm' ? 24 : size === 'md' ? 64 : 96}
        height={size === 'sm' ? 24 : size === 'md' ? 64 : 96}
        className="w-full h-full object-contain"
        priority
      />
    </div>
  )
}

