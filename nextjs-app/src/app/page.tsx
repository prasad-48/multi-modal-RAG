import { ChatInterface } from "@/components/ui/ChatInterface";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-100 dark:bg-gray-900 p-4">
      <div className="w-full max-w-2xl">
        <h1 className="text-4xl font-bold text-center mb-6 text-gray-800 dark:text-gray-200">
          Chat With Your Document
        </h1>
        <ChatInterface />
      </div>
    </main>
  );
}