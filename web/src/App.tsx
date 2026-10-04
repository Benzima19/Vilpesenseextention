import logo from './assets/vilpe-logo.svg'

export default function App() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-[440px] flex-col items-center justify-center gap-6 p-6">
      <img src={logo} alt="VILPE" className="h-8" />
      <h1 className="text-2xl font-semibold">Is my building OK?</h1>
      <p className="font-mono text-xs uppercase tracking-widest text-vilpe-blue">
        VILPE Guardian
      </p>
    </main>
  )
}
