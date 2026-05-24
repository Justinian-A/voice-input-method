import 'package:flutter/material.dart';
import '../services/voice_service.dart';

class SettingsPage extends StatefulWidget {
  final VoiceService voiceService;
  const SettingsPage({super.key, required this.voiceService});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  final _apiKeyController = TextEditingController();
  final _secretKeyController = TextEditingController();
  final _hostController = TextEditingController();
  final _portController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _apiKeyController.text = widget.voiceService.baiduApiKey;
    _secretKeyController.text = widget.voiceService.baiduSecretKey;
    _hostController.text = widget.voiceService.serverHost;
    _portController.text = widget.voiceService.serverPort.toString();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('设置')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 语音识别设置
          _buildSection('语音识别'),
          ListTile(
            title: const Text('语言'),
            subtitle: const Text('选择识别语言'),
            trailing: DropdownButton<String>(
              value: widget.voiceService.language,
              onChanged: (val) {
                if (val != null) {
                  setState(() => widget.voiceService.setLanguage(val));
                }
              },
              items: const [
                DropdownMenuItem(value: 'zh-CN', child: Text('中文')),
                DropdownMenuItem(value: 'en-US', child: Text('English')),
                DropdownMenuItem(value: 'yue', child: Text('粤语')),
              ],
            ),
          ),
          SwitchListTile(
            title: const Text('优先在线识别'),
            subtitle: const Text('关闭时使用离线Whisper模型'),
            value: widget.voiceService.preferOnline,
            onChanged: (val) => widget.voiceService.setPreferOnline(val),
          ),

          const Divider(),

          // 百度API设置
          _buildSection('百度语音识别API'),
          TextField(
            controller: _apiKeyController,
            decoration: const InputDecoration(
              labelText: 'API Key',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _secretKeyController,
            decoration: const InputDecoration(
              labelText: 'Secret Key',
              border: OutlineInputBorder(),
            ),
            obscureText: true,
          ),
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed: () {
              widget.voiceService.setApiKeys(
                _apiKeyController.text.trim(),
                _secretKeyController.text.trim(),
              );
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('API设置已保存')),
              );
            },
            child: const Text('保存API设置'),
          ),

          const Divider(),

          // 服务器设置
          _buildSection('服务连接'),
          TextField(
            controller: _hostController,
            decoration: const InputDecoration(
              labelText: '服务器地址',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _portController,
            decoration: const InputDecoration(
              labelText: '端口',
              border: OutlineInputBorder(),
            ),
            keyboardType: TextInputType.number,
          ),
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed: () {
              widget.voiceService.setServer(
                _hostController.text.trim(),
                int.tryParse(_portController.text.trim()) ?? 8765,
              );
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('服务器设置已保存')),
              );
            },
            child: const Text('保存连接设置'),
          ),

          const Divider(),

          // 状态信息
          _buildSection('系统状态'),
          ListTile(
            title: const Text('在线识别'),
            trailing: Icon(
              widget.voiceService.onlineAvailable
                  ? Icons.check_circle
                  : Icons.cancel,
              color: widget.voiceService.onlineAvailable
                  ? Colors.green
                  : Colors.red,
            ),
          ),
          ListTile(
            title: const Text('离线识别'),
            trailing: Icon(
              widget.voiceService.offlineAvailable
                  ? Icons.check_circle
                  : Icons.cancel,
              color: widget.voiceService.offlineAvailable
                  ? Colors.green
                  : Colors.red,
            ),
          ),
          ListTile(
            title: const Text('版本'),
            subtitle: const Text('语声 MVP v0.1.0'),
          ),
        ],
      ),
    );
  }

  Widget _buildSection(String title) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Text(
          title,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Theme.of(context).colorScheme.primary,
          ),
        ),
      );
}
