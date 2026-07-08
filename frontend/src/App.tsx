import { useState } from 'react'
import { 
  Wand2, 
  Image as ImageIcon, 
  Sparkles, 
  Upload, 
  Palette,
  Layers,
  MessageSquare,
  Download,
  Trash2,
  Maximize2,
  Star,
  RefreshCw,
  Eye
} from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

interface GeneratedImage {
  id: string
  url: string
  prompt: string
  createdAt: Date
}

interface AestheticEvaluation {
  overall_score: number
  composition?: {
    rule_of_thirds: number
    symmetry: number
    balance: number
  }
  color_analysis?: {
    dominant_colors: number[]
    color_harmony: number
    saturation_level: string
  }
  suggestions: string[]
}

function App() {
  const [activeTab, setActiveTab] = useState<'generate' | 'edit' | 'redesign' | 'evaluate'>('generate')
  const [prompt, setPrompt] = useState('')
  const [style, setStyle] = useState('photorealistic')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([])
  const [selectedImage, setSelectedImage] = useState<GeneratedImage | null>(null)
  const [editInstruction, setEditInstruction] = useState('')
  const [redesignStyle, setRedesignStyle] = useState('')
  const [evaluation, setEvaluation] = useState<AestheticEvaluation | null>(null)
  const [isEvaluating, setIsEvaluating] = useState(false)

  const styles = [
    { value: 'photorealistic', label: '写实风格', icon: '📷' },
    { value: 'illustration', label: '插画风格', icon: '🎨' },
    { value: 'minimalist', label: '极简主义', icon: '⬜' },
    { value: 'abstract', label: '抽象艺术', icon: '🌀' },
    { value: 'watercolor', label: '水彩画', icon: '💧' },
    { value: 'oil_painting', label: '油画', icon: '🖼️' },
    { value: 'digital_art', label: '数字艺术', icon: '💻' },
    { value: 'anime', label: '动漫风格', icon: '🎭' },
    { value: 'concept_art', label: '概念艺术', icon: '🎪' },
    { value: 'architectural', label: '建筑设计', icon: '🏛️' },
  ]

  const handleGenerate = async () => {
    if (!prompt.trim()) return

    setIsGenerating(true)
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/generate`, {
        prompt,
        style,
        width: 1024,
        height: 1024,
        num_inference_steps: 30,
        guidance_scale: 7.5,
        num_images: 2
      })

      if (response.data.success) {
        const newImages = response.data.image_ids.map((id: string) => ({
          id,
          url: `${API_BASE_URL}/api/v1/images/${id}`,
          prompt,
          createdAt: new Date()
        }))
        setGeneratedImages(prev => [...newImages, ...prev])
      }
    } catch (error) {
      console.error('生成失败:', error)
      alert('生成失败，请重试')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleEdit = async () => {
    if (!selectedImage || !editInstruction.trim()) return

    setIsGenerating(true)
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/edit`, {
        image_id: selectedImage.id,
        instruction: editInstruction,
        strength: 0.75
      })

      if (response.data.success) {
        const editedImage = {
          id: response.data.image_id,
          url: `${API_BASE_URL}/api/v1/images/${response.data.image_id}`,
          prompt: editInstruction,
          createdAt: new Date()
        }
        setGeneratedImages(prev => [editedImage, ...prev])
        setSelectedImage(editedImage)
        setEditInstruction('')
      }
    } catch (error) {
      console.error('编辑失败:', error)
      alert('编辑失败，请重试')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleRedesign = async () => {
    if (!selectedImage || !redesignStyle.trim()) return

    setIsGenerating(true)
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/redesign`, {
        image_id: selectedImage.id,
        style_description: redesignStyle,
        preserve_elements: [],
        num_variants: 3
      })

      if (response.data.success) {
        const newImages = response.data.image_ids.map((id: string) => ({
          id,
          url: `${API_BASE_URL}/api/v1/images/${id}`,
          prompt: `重设计：${redesignStyle}`,
          createdAt: new Date()
        }))
        setGeneratedImages(prev => [...newImages, ...prev])
        setRedesignStyle('')
      }
    } catch (error) {
      console.error('重设计失败:', error)
      alert('重设计失败，请重试')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleEvaluate = async () => {
    if (!selectedImage) return

    setIsEvaluating(true)
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/aesthetic/evaluate`, {
        image_id: selectedImage.id
      })

      if (response.data.success) {
        setEvaluation(response.data.evaluation)
      }
    } catch (error) {
      console.error('评估失败:', error)
      alert('评估失败，请重试')
    } finally {
      setIsEvaluating(false)
    }
  }

  const handleDelete = async (imageId: string) => {
    try {
      await axios.delete(`${API_BASE_URL}/api/v1/images/${imageId}`)
      setGeneratedImages(prev => prev.filter(img => img.id !== imageId))
      if (selectedImage?.id === imageId) {
        setSelectedImage(null)
      }
    } catch (error) {
      console.error('删除失败:', error)
    }
  }

  const handleDownload = async (imageUrl: string, imageId: string) => {
    try {
      const response = await axios.get(imageUrl, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `visioncraft-${imageId}.png`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('下载失败:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  VisionCraft
                </h1>
                <p className="text-xs text-slate-500">AI 驱动的智能设计软件</p>
              </div>
            </div>
            
            <nav className="flex items-center space-x-1">
              <button
                onClick={() => { setActiveTab('generate'); setEvaluation(null); }}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'generate'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Wand2 className="w-4 h-4" />
                  <span>文生图</span>
                </div>
              </button>
              
              <button
                onClick={() => { setActiveTab('edit'); setEvaluation(null); }}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'edit'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Palette className="w-4 h-4" />
                  <span>智能编辑</span>
                </div>
              </button>
              
              <button
                onClick={() => { setActiveTab('redesign'); setEvaluation(null); }}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'redesign'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Layers className="w-4 h-4" />
                  <span>视觉重设计</span>
                </div>
              </button>

              <button
                onClick={() => setActiveTab('evaluate')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'evaluate'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Star className="w-4 h-4" />
                  <span>审美评估</span>
                </div>
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Panel - Controls */}
          <div className="lg:col-span-1 space-y-6">
            {/* Prompt Input */}
            {(activeTab === 'generate' || activeTab === 'edit' || activeTab === 'redesign') && (
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                {activeTab === 'generate' && (
                  <>
                    <label className="block text-sm font-medium text-slate-700 mb-3">
                      <MessageSquare className="w-4 h-4 inline mr-2" />
                      描述你的创意
                    </label>
                    <textarea
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      placeholder="例如：一个现代简约风格的客厅设计，大面积落地窗，自然光线充足，绿植点缀..."
                      className="w-full h-32 px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-all"
                    />
                    
                    {/* Style Selection */}
                    <div className="mt-4">
                      <label className="block text-sm font-medium text-slate-700 mb-3">
                        <Palette className="w-4 h-4 inline mr-2" />
                        选择风格
                      </label>
                      <div className="grid grid-cols-2 gap-2">
                        {styles.map((s) => (
                          <button
                            key={s.value}
                            onClick={() => setStyle(s.value)}
                            className={`px-3 py-2 rounded-lg text-sm font-medium transition-all border-2 ${
                              style === s.value
                                ? 'border-blue-500 bg-blue-50 text-blue-700'
                                : 'border-slate-200 hover:border-slate-300 text-slate-600'
                            }`}
                          >
                            <span className="mr-2">{s.icon}</span>
                            {s.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Generate Button */}
                    <button
                      onClick={handleGenerate}
                      disabled={isGenerating || !prompt.trim()}
                      className="w-full mt-6 py-3 px-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2"
                    >
                      {isGenerating ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>生成中...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-5 h-5" />
                          <span>开始创作</span>
                        </>
                      )}
                    </button>
                  </>
                )}

                {activeTab === 'edit' && selectedImage && (
                  <>
                    <label className="block text-sm font-medium text-slate-700 mb-3">
                      <MessageSquare className="w-4 h-4 inline mr-2" />
                      编辑指令
                    </label>
                    <textarea
                      value={editInstruction}
                      onChange={(e) => setEditInstruction(e.target.value)}
                      placeholder="例如：将沙发换成深蓝色的皮质沙发，添加一些装饰画..."
                      className="w-full h-24 px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-all"
                    />
                    
                    <button
                      onClick={handleEdit}
                      disabled={isGenerating || !editInstruction.trim()}
                      className="w-full mt-4 py-3 px-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-medium hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2"
                    >
                      {isGenerating ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>编辑中...</span>
                        </>
                      ) : (
                        <>
                          <Wand2 className="w-5 h-5" />
                          <span>应用编辑</span>
                        </>
                      )}
                    </button>
                  </>
                )}

                {activeTab === 'redesign' && selectedImage && (
                  <>
                    <label className="block text-sm font-medium text-slate-700 mb-3">
                      <Layers className="w-4 h-4 inline mr-2" />
                      目标风格描述
                    </label>
                    <textarea
                      value={redesignStyle}
                      onChange={(e) => setRedesignStyle(e.target.value)}
                      placeholder="例如：赛博朋克风格，霓虹灯光，未来科技感..."
                      className="w-full h-24 px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-all"
                    />
                    
                    <button
                      onClick={handleRedesign}
                      disabled={isGenerating || !redesignStyle.trim()}
                      className="w-full mt-4 py-3 px-4 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-xl font-medium hover:from-purple-600 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2"
                    >
                      {isGenerating ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>重设计中...</span>
                        </>
                      ) : (
                        <>
                          <RefreshCw className="w-5 h-5" />
                          <span>生成设计方案</span>
                        </>
                      )}
                    </button>
                  </>
                )}

                {activeTab === 'edit' && !selectedImage && (
                  <div className="text-center py-8 text-slate-500">
                    <ImageIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>请先在右侧选择一张图片进行编辑</p>
                  </div>
                )}

                {activeTab === 'redesign' && !selectedImage && (
                  <div className="text-center py-8 text-slate-500">
                    <Layers className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>请先在右侧选择一张图片进行重设计</p>
                  </div>
                )}
              </div>
            )}

            {/* Evaluation Panel */}
            {activeTab === 'evaluate' && (
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center">
                  <Star className="w-5 h-5 mr-2 text-yellow-500" />
                  审美评估
                </h3>
                
                {selectedImage ? (
                  <>
                    <button
                      onClick={handleEvaluate}
                      disabled={isEvaluating}
                      className="w-full py-3 px-4 bg-gradient-to-r from-yellow-500 to-orange-600 text-white rounded-xl font-medium hover:from-yellow-600 hover:to-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2"
                    >
                      {isEvaluating ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>评估中...</span>
                        </>
                      ) : (
                        <>
                          <Eye className="w-5 h-5" />
                          <span>开始评估</span>
                        </>
                      )}
                    </button>

                    {evaluation && (
                      <div className="mt-6 space-y-4 animate-fade-in">
                        <div className="text-center">
                          <div className="text-4xl font-bold text-yellow-500">
                            {evaluation.overall_score}/10
                          </div>
                          <p className="text-sm text-slate-500">整体审美评分</p>
                        </div>

                        {evaluation.composition && (
                          <div>
                            <h4 className="font-medium text-slate-700 mb-2">构图分析</h4>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span>三分法:</span>
                                <span className="text-blue-600">{(evaluation.composition.rule_of_thirds * 10).toFixed(1)}/10</span>
                              </div>
                              <div className="flex justify-between">
                                <span>对称性:</span>
                                <span className="text-blue-600">{(evaluation.composition.symmetry * 10).toFixed(1)}/10</span>
                              </div>
                              <div className="flex justify-between">
                                <span>平衡感:</span>
                                <span className="text-blue-600">{(evaluation.composition.balance * 10).toFixed(1)}/10</span>
                              </div>
                            </div>
                          </div>
                        )}

                        {evaluation.color_analysis && (
                          <div>
                            <h4 className="font-medium text-slate-700 mb-2">色彩分析</h4>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span>色彩和谐度:</span>
                                <span className="text-purple-600">{(evaluation.color_analysis.color_harmony * 10).toFixed(1)}/10</span>
                              </div>
                              <div className="flex justify-between">
                                <span>饱和度:</span>
                                <span className="text-purple-600">{evaluation.color_analysis.saturation_level}</span>
                              </div>
                            </div>
                          </div>
                        )}

                        <div>
                          <h4 className="font-medium text-slate-700 mb-2">改进建议</h4>
                          <ul className="space-y-1 text-sm text-slate-600">
                            {evaluation.suggestions.map((suggestion, index) => (
                              <li key={index} className="flex items-start">
                                <span className="text-green-500 mr-2">•</span>
                                {suggestion}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <Star className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>请先在右侧选择一张图片进行评估</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Panel - Gallery */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 min-h-[600px]">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-slate-800">
                  <ImageIcon className="w-5 h-5 inline mr-2" />
                  作品画廊
                </h2>
                {generatedImages.length > 0 && (
                  <span className="text-sm text-slate-500">
                    {generatedImages.length} 个作品
                  </span>
                )}
              </div>

              {generatedImages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-96 text-slate-400">
                  <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                    <Upload className="w-10 h-10" />
                  </div>
                  <p className="text-lg font-medium">还没有作品</p>
                  <p className="text-sm mt-2">输入描述，开始你的第一次 AI 创作</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {generatedImages.map((img) => (
                    <div
                      key={img.id}
                      onClick={() => setSelectedImage(img)}
                      className={`group relative aspect-square rounded-xl overflow-hidden cursor-pointer transition-all ${
                        selectedImage?.id === img.id
                          ? 'ring-4 ring-blue-500 shadow-lg'
                          : 'hover:shadow-md'
                      }`}
                    >
                      <img
                        src={img.url}
                        alt={img.prompt}
                        className="w-full h-full object-cover transition-transform group-hover:scale-105"
                        loading="lazy"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="absolute bottom-0 left-0 right-0 p-4">
                          <p className="text-white text-sm line-clamp-2">
                            {img.prompt}
                          </p>
                        </div>
                      </div>
                      {selectedImage?.id === img.id && (
                        <div className="absolute top-2 right-2 flex space-x-2">
                          <button 
                            onClick={(e) => { e.stopPropagation(); handleDownload(img.url, img.id); }}
                            className="p-2 bg-white/90 rounded-lg hover:bg-white transition-colors"
                          >
                            <Download className="w-4 h-4 text-slate-700" />
                          </button>
                          <button 
                            onClick={(e) => { e.stopPropagation(); handleDelete(img.id); }}
                            className="p-2 bg-white/90 rounded-lg hover:bg-red-100 transition-colors"
                          >
                            <Trash2 className="w-4 h-4 text-red-600" />
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
