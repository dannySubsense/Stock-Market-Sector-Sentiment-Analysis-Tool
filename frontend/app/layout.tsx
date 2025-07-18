import React from 'react'
import './globals.css'

export const metadata = {
  title: 'Market Sector Sentiment Analysis Tool',
  description: 'AI-powered sector-first sentiment analysis platform for small-cap traders',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-bg-primary text-text-primary min-h-screen">
        <div className="container mx-auto px-4 py-8">
          {children}
        </div>
      </body>
    </html>
  )
} 