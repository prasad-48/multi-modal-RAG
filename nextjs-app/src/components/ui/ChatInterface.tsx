'use client';

import { useState, useRef, FormEvent, ChangeEvent, useEffect, memo } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Toaster, toast } from "sonner";
import { LoaderCircle, Send } from "lucide-react";

// --- Type Definitions ---
type Message = {
    role: 'user' | 'assistant';
    content: string;
};

type UploadStatus = {
    status: 'idle' | 'uploading' | 'processing' | 'completed' | 'failed';
    message: string;
    progress: number;
};

const PYTHON_API_URL = process.env.NEXT_PUBLIC_PYTHON_API_URL;

// --- Child Components (Defined Outside) ---

interface FileUploaderProps {
    uploadStatus: UploadStatus;
    handleFileUpload: (event: ChangeEvent<HTMLInputElement>) => void;
}

const FileUploader = memo(({ uploadStatus, handleFileUpload }: FileUploaderProps) => {
    const isUploadingOrProcessing = uploadStatus.status === 'processing' || uploadStatus.status === 'uploading';
    return (
        <div className="flex flex-col items-center justify-center space-y-4 rounded-lg border-2 border-dashed border-gray-300 p-8 text-center">
            <p className="text-gray-500">{uploadStatus.message}</p>
            {uploadStatus.status === 'processing' && (
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${uploadStatus.progress}%` }}></div>
                </div>
            )}
            <Input
                id="file-upload"
                type="file"
                onChange={handleFileUpload}
                className="hidden"
                disabled={isUploadingOrProcessing}
            />
            <Button asChild variant="outline">
                <label
                    htmlFor="file-upload"
                    className={`cursor-pointer ${isUploadingOrProcessing ? 'cursor-not-allowed opacity-50' : ''}`}
                >
                    {isUploadingOrProcessing ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : null}
                    {uploadStatus.status === 'idle' || uploadStatus.status === 'failed' ? "Select File" : "Processing..."}
                </label>
            </Button>
            <p className="text-xs text-gray-400">Supports PDF, DOCX, TXT. Max 50MB.</p>
        </div>
    );
});
FileUploader.displayName = 'FileUploader';


interface ChatWindowProps {
    messages: Message[];
    chatContainerRef: React.RefObject<HTMLDivElement | null>;
    handleSendMessage: (e: FormEvent) => Promise<void>;
    inputValue: string;
    setInputValue: (value: string) => void;
    isLoading: boolean;
}

const ChatWindow = memo(({ messages, chatContainerRef, handleSendMessage, inputValue, setInputValue, isLoading }: ChatWindowProps) => {
    return (
        <div className="flex flex-col space-y-4">
            <div ref={chatContainerRef} className="h-96 overflow-y-auto rounded-md border p-4 space-y-4">
                {messages.map((msg, index) => (
                    <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-xs md:max-w-md lg:max-w-lg rounded-lg px-4 py-2 ${msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}`}>
                            <p style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                        </div>
                    </div>
                ))}
            </div>
            <form onSubmit={handleSendMessage} className="flex items-center space-x-2">
                <Input
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Ask a question about your document..."
                    disabled={isLoading}
                    autoFocus
                />
                <Button type="submit" disabled={isLoading || !inputValue.trim()}>
                    {isLoading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </Button>
            </form>
        </div>
    );
});
ChatWindow.displayName = 'ChatWindow';


// --- Main Component ---
export function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [collectionName, setCollectionName] = useState<string | null>(null);
    const [taskId, setTaskId] = useState<string | null>(null);
    const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
        status: 'idle',
        message: 'Upload a document to start chatting',
        progress: 0,
    });
    const chatContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);

    useEffect(() => {
        if (taskId && uploadStatus.status === 'processing') {
            const interval = setInterval(async () => {
                try {
                    const response = await axios.get(`${PYTHON_API_URL}/api/status/${taskId}`);
                    const { status, message, progress, collection_name } = response.data;

                    setUploadStatus({ status, message, progress });

                    if (status === 'completed') {
                        clearInterval(interval);
                        setCollectionName(collection_name);
                        toast.success(message || "Document processed successfully!");
                        setTaskId(null);
                    } else if (status === 'failed') {
                        clearInterval(interval);
                        toast.error(message || "Processing failed.");
                        setTaskId(null);
                    }
                } catch {
                    clearInterval(interval);
                    toast.error("Could not get processing status.");
                    setUploadStatus({ status: 'failed', message: 'Polling failed.', progress: 0 });
                    setTaskId(null);
                }
            }, 2000);

            return () => clearInterval(interval);
        }
    }, [taskId, uploadStatus.status]);

    const handleFileUpload = async (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setUploadStatus({ status: 'uploading', message: `Uploading ${file.name}...`, progress: 0 });
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post(`${PYTHON_API_URL}/api/upload`, formData);
            setTaskId(response.data.task_id);
            setUploadStatus({ status: 'processing', message: 'Upload complete. Processing...', progress: 5 });
            toast.info("File uploaded, starting processing...");
        } catch (error: unknown) {
            const errorMessage = axios.isAxiosError(error)
                ? error.response?.data?.detail || error.message || "File upload failed."
                : "File upload failed.";
        
            const message =
                typeof errorMessage === 'string'
                    ? errorMessage
                    : "File upload failed.";
        
            setUploadStatus({
                status: 'failed',
                message,
                progress: 0,
            });
        
            toast.error(message);
        }
    };

    const handleSendMessage = async (e: FormEvent) => {
        e.preventDefault();
        if (!inputValue.trim() || !collectionName || isLoading) return;

        const userMessage: Message = { role: 'user', content: inputValue };
        setMessages((prev) => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            const response = await axios.post(`${PYTHON_API_URL}/api/chat`, {
                query: userMessage.content,
                collection_name: collectionName,
            });
            const assistantMessage: Message = { role: 'assistant', content: response.data.response };
            setMessages((prev) => [...prev, assistantMessage]);
        } catch  {
            const errorMessage: Message = { role: 'assistant', content: "Sorry, I ran into an error. Please try again." };
            setMessages((prev) => [...prev, errorMessage]);
            toast.error("An error occurred while getting the response.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Card className="w-full">
            <CardHeader>
                <CardTitle>Chat with Document</CardTitle>
                <CardDescription>Upload a document and ask questions about its content.</CardDescription>
            </CardHeader>
            <CardContent>
                {uploadStatus.status === 'completed' ? (
                    <ChatWindow
                        messages={messages}
                        chatContainerRef={chatContainerRef}
                        handleSendMessage={handleSendMessage}
                        inputValue={inputValue}
                        setInputValue={setInputValue}
                        isLoading={isLoading}
                    />
                ) : (
                    <FileUploader uploadStatus={uploadStatus} handleFileUpload={handleFileUpload} />
                )}
            </CardContent>
            <Toaster richColors position="top-right" />
        </Card>
    );
}