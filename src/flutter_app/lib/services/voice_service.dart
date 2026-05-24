import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

enum VoiceState { idle, listening, processing, error }

class VoiceService extends ChangeNotifier {
  WebSocketChannel? _channel;
  VoiceState _state = VoiceState.idle;
  String _recognizedText = '';
  double _audioLevel = 0.0;
  String _errorMessage = '';
  bool _onlineAvailable = true;
  bool _offlineAvailable = false;
  String _language = 'zh-CN';
  bool _preferOnline = true;
  String _serverHost = '127.0.0.1';
  int _serverPort = 8765;

  // Settings
  String _baiduApiKey = '';
  String _baiduSecretKey = '';

  VoiceState get state => _state;
  String get recognizedText => _recognizedText;
  double get audioLevel => _audioLevel;
  String get errorMessage => _errorMessage;
  bool get onlineAvailable => _onlineAvailable;
  bool get offlineAvailable => _offlineAvailable;
  String get language => _language;
  bool get preferOnline => _preferOnline;
  String get baiduApiKey => _baiduApiKey;
  String get baiduSecretKey => _baiduSecretKey;
  String get serverHost => _serverHost;
  int get serverPort => _serverPort;

  final StreamController<String> _commandController = StreamController.broadcast();
  Stream<String> get commandStream => _commandController.stream;

  void setServer(String host, int port) {
    _serverHost = host;
    _serverPort = port;
  }

  void setApiKeys(String key, String secret) {
    _baiduApiKey = key;
    _baiduSecretKey = secret;
    _sendCommand('update_settings', {
      'api_key': key,
      'secret_key': secret,
    });
  }

  void setLanguage(String lang) {
    _language = lang;
  }

  void setPreferOnline(bool online) {
    _preferOnline = online;
  }

  Future<bool> connect() async {
    try {
      final uri = Uri(
        scheme: 'ws',
        host: _serverHost,
        port: _serverPort,
      );
      _channel = WebSocketChannel.connect(uri);
      await _channel!.ready;

      _channel!.stream.listen(
        _handleMessage,
        onError: (error) {
          _state = VoiceState.error;
          _errorMessage = '连接错误: $error';
          notifyListeners();
        },
        onDone: () {
          _state = VoiceState.idle;
          notifyListeners();
        },
      );
      return true;
    } catch (e) {
      _errorMessage = '无法连接到服务: $e';
      return false;
    }
  }

  void _handleMessage(dynamic data) {
    try {
      final msg = jsonDecode(data as String);
      final event = msg['event'] as String?;

      switch (event) {
        case 'audio_level':
          _audioLevel = (msg['data']?['level'] ?? 0.0).toDouble();
          if (_state == VoiceState.listening) {
            _state = VoiceState.processing;
          }
          break;
        case 'text':
          _recognizedText = msg['data']?['text'] ?? '';
          _state = VoiceState.idle;
          // 自动复制到剪贴板供用户粘贴
          break;
        case 'command':
          final cmd = msg['data'];
          _commandController.add(jsonEncode(cmd));
          _recognizedText = '';
          break;
        case 'error':
          _errorMessage = msg['data']?['message'] ?? '未知错误';
          break;
        case 'status':
          _onlineAvailable = msg['data']?['online_available'] ?? true;
          _offlineAvailable = msg['data']?['offline_available'] ?? false;
          break;
        case 'stopped':
          _state = VoiceState.idle;
          break;
      }
      notifyListeners();
    } catch (_) {
      // 忽略解析错误
    }
  }

  void startListening() {
    if (_channel == null) return;
    _state = VoiceState.listening;
    _recognizedText = '';
    _errorMessage = '';
    _sendCommand('start_recognition', {
      'language': _language,
      'online': _preferOnline,
    });
    notifyListeners();
  }

  void stopListening() {
    _state = VoiceState.idle;
    _sendCommand('stop_recognition', {});
    notifyListeners();
  }

  void _sendCommand(String command, Map<String, dynamic> data) {
    _channel?.sink.add(jsonEncode({
      'command': command,
      ...data,
    }));
  }

  @override
  void dispose() {
    _commandController.close();
    _channel?.sink.close();
    super.dispose();
  }
}
