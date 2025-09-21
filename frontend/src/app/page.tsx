import { redirect } from 'next/navigation';

export default function Home() {
  // Redirect to dashboard as this is the main entry point for HeatGuard Pro
  redirect('/dashboard');
}
