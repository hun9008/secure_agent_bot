'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { X } from "lucide-react"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm';

export function SecuritiesAgentDemoComponent() {
  const [showReport, setShowReport] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const [reportContent, setReportContent] = useState('')
  const [chatMessages, setChatMessages] = useState<{ role: 'user' | 'bot', content: string }[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const fetchReport = async () => {
    try {
      // 서버에서 JSON 응답을 받기 위해 response.json() 사용
      const response = await fetch('http://sinhan.hunian.site/get_report')
      const data = await response.json()  // 응답을 JSON으로 파싱
  
      // data 객체에서 response 필드만 추출하여 reportContent에 저장
      setReportContent(data.response)  // reportContent에 response의 내용만 저장
      setShowReport(true)
    } catch (error) {
      console.error('Error fetching report:', error)
    }
  }

  const sendChatMessage = async () => {
    if (!inputMessage.trim()) return;
  
    // 사용자가 입력한 메시지를 채팅 기록에 추가
    setChatMessages(prev => [...prev, { role: 'user', content: inputMessage }]);
    setInputMessage('');
    setLoading(true);
  
    try {
      // 이전 메시지를 하나의 문자열로 구성하여 prev_chat에 전달
      const prevChat = chatMessages.map(msg => `${msg.role}: ${msg.content}`).join('\n');
  
      // 서버에 보낼 데이터 구성
      const payload = {
        prev_chat: prevChat,  // 이전 대화 내용
        prompt: inputMessage  // 사용자가 입력한 새로운 메시지
      };
  
      // 서버에 POST 요청
      const response = await fetch('http://sinhan.hunian.site/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),  // 새로운 형식으로 요청 본문 전송
      });
  
      const data = await response.json();
  
      // 서버의 응답을 채팅 기록에 추가
      setChatMessages(prev => [...prev, { role: 'bot', content: data.response }]);
    } catch (error) {
      console.error('Error sending chat message:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const interval = setInterval(() => {
      const bubbles = document.querySelectorAll('.bubble')
      bubbles.forEach((bubble) => {
        const x = Math.random() * 100
        const y = Math.random() * 100
        ;(bubble as HTMLElement).style.left = `${x}%`
        ;(bubble as HTMLElement).style.top = `${y}%`
      })
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-blue-900 to-black text-white flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {[...Array(10)].map((_, i) => (
        <div key={i} className="bubble absolute w-4 h-4 bg-blue-500 rounded-full opacity-20" style={{
          left: `${Math.random() * 100}%`,
          top: `${Math.random() * 100}%`,
          transition: 'all 3s ease-in-out',
        }} />
      ))}
      <div className="text-center z-10">
        <h1 className="text-4xl font-bold mb-2 text-blue-300">Financial Agent Chat</h1>
        <p className="text-xl mb-8 text-blue-200">Demo Page</p>
        <div className="bg-black bg-opacity-50 p-6 rounded-lg mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-blue-400">Financial Agent Chat</h2>
          <p className="text-lg mb-2">Example Case:</p>
          <p className="text-xl mb-4 text-blue-300">User 1 belonging to Cluster 0</p>
          <p className="text-sm mb-6 text-gray-400">* This is an example user for demo purposes. Personalized information will be displayed in the actual service.</p>
          <div className="space-x-4">
            <Button onClick={fetchReport} className="bg-blue-600 hover:bg-blue-700 transition-colors duration-300">
              Report
            </Button>
            <Button onClick={() => setShowChat(true)} className="bg-blue-600 hover:bg-blue-700 transition-colors duration-300">
              Chat
            </Button>
          </div>
        </div>
      </div>

      {/* Report Overlay */}
      {showReport && (
  <Card className="fixed inset-4 z-50 bg-gray-900 text-white overflow-auto">
    <CardContent className="p-6">
      <Button onClick={() => setShowReport(false)} className="absolute top-2 right-2 bg-transparent hover:bg-gray-800">
        <X className="h-6 w-6" />
      </Button>
      <h2 className="text-2xl font-bold mb-4 text-blue-500">Report</h2>
      {/* \n을 \n\n로 변환하여 마크다운 적용 */}
      <ReactMarkdown className="prose prose-invert" remarkPlugins={[remarkGfm]}>
        {reportContent.replace(/\n/g, '\n\n')} 
      </ReactMarkdown>
    </CardContent>
  </Card>
)}

      {/* Chat Overlay */}
      {showChat && (
        <Card className="fixed inset-4 z-50 bg-gray-900 text-white flex flex-col w-3/5 mx-auto">
          <CardContent className="flex-1 overflow-auto p-6">
            <Button onClick={() => setShowChat(false)} className="absolute top-2 right-2 bg-transparent hover:bg-gray-800">
              <X className="h-6 w-6" />
            </Button>
            <h2 className="text-2xl font-bold mb-4 text-blue-500">Chat</h2>
            <div className="space-y-4 mb-4">
              {chatMessages.map((msg, index) => (
                <div key={index} className={`p-2 rounded-lg ${msg.role === 'user' ? 'bg-blue-600 ml-auto w-3/5' : 'bg-gray-700 w-3/5'}`}>
                  {msg.content}
                </div>
              ))}
              {/* 응답을 기다리는 동안 "Thinking..." 표시 */}
              {loading && (
                <div className="p-2 rounded-lg bg-gray-700 w-3/5">
                  Thinking...
                </div>
              )}
            </div>
            <div className="flex mt-auto">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                className="flex-1 p-2 bg-gray-800 text-white rounded-l-lg focus:outline-none"
                placeholder="Type your message..."
              />
              <Button onClick={sendChatMessage} className="bg-blue-600 hover:bg-blue-700 rounded-l-none">Send</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}