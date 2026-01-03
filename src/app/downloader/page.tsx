'use client';

import { useState } from 'react';
import Navbar from '@/components/Navbar';
import zh from '@/locales/zh.json';

export default function DownloaderPage() {
  const [lang] = useState(zh); // 默认使用中文还原
  const [url, setUrl] = useState('');
  const [service, setService] = useState('');

  return (
    <main>
      <Navbar lang={lang} />
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-6 md:p-8">
            <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <i className="bi bi-cloud-download text-blue-600"></i>
              {lang.app_title}
            </h1>
            
            <p className="text-slate-600 mb-8 leading-relaxed">
              {lang.intro_text}
            </p>

            <form className="space-y-6">
              {/* URL Input */}
              <div>
                <label className="block text-sm font-semibold mb-2">{lang.url_label}</label>
                <input 
                  type="text" 
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder={lang.url_placeholder}
                  className="w-full px-4 py-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                />
              </div>

              {/* Service Selection */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold mb-2">上传服务</label>
                  <select 
                    value={service}
                    onChange={(e) => setService(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg border border-slate-300 outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                  >
                    <option value="">-- 请选择服务 --</option>
                    <option value="gofile">Gofile.io</option>
                    <option value="webdav">WebDAV</option>
                    <option value="s3">S3 兼容存储</option>
                  </select>
                </div>
              </div>

              {/* Advanced Options (Collapsible simulation) */}
              <div className="border-t pt-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <i className="bi bi-sliders"></i>
                  {lang.advanced_options_title}
                </h3>
                {/* 更多选项将在这里徒步还原 */}
                <div className="bg-slate-50 p-4 rounded-lg text-slate-500 text-sm">
                  高级选项正在按计划还原中...
                </div>
              </div>

              {/* Submit Button */}
              <button 
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-200 transition-all transform active:scale-[0.98]"
              >
                <i className="bi bi-play-fill me-2"></i>
                {lang.start_download_button}
              </button>
            </form>
          </div>
        </div>
      </div>
    </main>
  );
}
