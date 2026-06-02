import './globals.css';

export const metadata = {
  title: 'Ad Simulator',
  description: 'AI 페르소나가 실제 사람처럼 광고에 반응합니다',
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
