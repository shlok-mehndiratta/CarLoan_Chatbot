import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/contract_model.dart';

class NegotiationChatScreen extends StatefulWidget {
  final int contractId;
  final String? contractName;

  const NegotiationChatScreen({
    super.key,
    required this.contractId,
    this.contractName,
  });

  @override
  State<NegotiationChatScreen> createState() => _NegotiationChatScreenState();
}

class _NegotiationChatScreenState extends State<NegotiationChatScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  int? _threadId;
  List<ChatMessage> _messages = [];
  List<NegotiationPoint> _negotiationPoints = [];
  bool _isInitializing = true;
  bool _isSending = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _startNegotiation();
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _startNegotiation() async {
    try {
      final thread = await _apiService.startNegotiation(widget.contractId);
      setState(() {
        _threadId = thread.threadId;
        _negotiationPoints = thread.negotiationPoints;
        _messages = [
          ChatMessage(role: 'assistant', content: thread.welcomeMessage),
        ];
        _isInitializing = false;
      });
      _scrollToBottom();
    } catch (e) {
      setState(() {
        _error = e.toString().replaceFirst('Exception: ', '');
        _isInitializing = false;
      });
    }
  }

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty || _threadId == null || _isSending) return;

    _messageController.clear();

    setState(() {
      _messages.add(ChatMessage(role: 'user', content: text));
      _isSending = true;
    });
    _scrollToBottom();

    try {
      final response = await _apiService.sendNegotiationMessage(_threadId!, text);
      setState(() {
        _messages.add(ChatMessage(role: 'assistant', content: response));
        _isSending = false;
      });
      _scrollToBottom();
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
        ));
        _isSending = false;
      });
      _scrollToBottom();
    }
  }

  Future<void> _generateEmail() async {
    if (_threadId == null) return;

    setState(() => _isSending = true);

    _messages.add(ChatMessage(role: 'user', content: '📧 Generate a negotiation email'));
    _scrollToBottom();

    try {
      final email = await _apiService.generateNegotiationEmail(
        widget.contractId,
        tone: 'professional',
      );
      setState(() {
        _messages.add(ChatMessage(role: 'assistant', content: '📧 Here\'s your negotiation email:\n\n$email'));
        _isSending = false;
      });
      _scrollToBottom();
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(role: 'assistant', content: 'Failed to generate email. Please try again.'));
        _isSending = false;
      });
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Negotiation Assistant', style: TextStyle(fontSize: 16)),
            Text(
              widget.contractName ?? 'Contract #${widget.contractId}',
              style: TextStyle(fontSize: 12, color: Colors.grey.shade400),
            ),
          ],
        ),
        elevation: 1,
        actions: [
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'email') _generateEmail();
              if (value == 'points') _showNegotiationPoints();
            },
            itemBuilder: (context) => [
              const PopupMenuItem(value: 'email', child: Row(
                children: [Icon(Icons.email, size: 20), SizedBox(width: 8), Text('Generate Email')],
              )),
              const PopupMenuItem(value: 'points', child: Row(
                children: [Icon(Icons.list, size: 20), SizedBox(width: 8), Text('View Key Points')],
              )),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          // Negotiation points chip bar
          if (_negotiationPoints.isNotEmpty)
            SizedBox(
              height: 42,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                itemCount: _negotiationPoints.length,
                itemBuilder: (context, i) {
                  final p = _negotiationPoints[i];
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ActionChip(
                      avatar: Icon(p.getSeverityIcon(), size: 16, color: p.getSeverityColor()),
                      label: Text(
                        p.category.replaceAll('_', ' '),
                        style: const TextStyle(fontSize: 12),
                      ),
                      onPressed: () => _sendQuickMessage(p),
                      backgroundColor: p.getSeverityColor().withOpacity(0.1),
                    ),
                  );
                },
              ),
            ),

          // Messages
          Expanded(
            child: _isInitializing
                ? const Center(child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                      Text('Setting up negotiation session...'),
                    ],
                  ))
                : _error != null
                    ? Center(child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.error_outline, size: 48, color: Colors.red),
                            const SizedBox(height: 12),
                            Text(_error!, textAlign: TextAlign.center),
                            const SizedBox(height: 16),
                            ElevatedButton(
                              onPressed: () { setState(() { _error = null; _isInitializing = true; }); _startNegotiation(); },
                              child: const Text('Retry'),
                            ),
                          ],
                        ),
                      ))
                    : ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        itemCount: _messages.length + (_isSending ? 1 : 0),
                        itemBuilder: (context, index) {
                          if (index == _messages.length) {
                            return _buildTypingIndicator(isDark);
                          }
                          return _buildMessageBubble(_messages[index], theme, isDark);
                        },
                      ),
          ),

          // Input bar
          Container(
            padding: EdgeInsets.fromLTRB(12, 8, 8, 8 + MediaQuery.of(context).padding.bottom),
            decoration: BoxDecoration(
              color: isDark ? Colors.grey.shade900 : Colors.white,
              boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 4, offset: const Offset(0, -1))],
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    maxLines: 3,
                    minLines: 1,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _sendMessage(),
                    decoration: InputDecoration(
                      hintText: 'Ask about your contract...',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                      filled: true,
                      fillColor: isDark ? Colors.grey.shade800 : Colors.grey.shade100,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                CircleAvatar(
                  backgroundColor: theme.primaryColor,
                  child: IconButton(
                    icon: const Icon(Icons.send, color: Colors.white, size: 20),
                    onPressed: _isSending ? null : _sendMessage,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage msg, ThemeData theme, bool isDark) {
    final isUser = msg.role == 'user';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            CircleAvatar(
              radius: 16,
              backgroundColor: theme.primaryColor.withOpacity(0.2),
              child: Icon(Icons.smart_toy, size: 18, color: theme.primaryColor),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: isUser
                    ? theme.primaryColor
                    : isDark ? Colors.grey.shade800 : Colors.grey.shade100,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(isUser ? 16 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 16),
                ),
              ),
              child: SelectableText(
                msg.content,
                style: TextStyle(
                  color: isUser ? Colors.white : null,
                  fontSize: 14,
                  height: 1.4,
                ),
              ),
            ),
          ),
          if (isUser) ...[
            const SizedBox(width: 8),
            CircleAvatar(
              radius: 16,
              backgroundColor: Colors.grey.shade300,
              child: const Icon(Icons.person, size: 18, color: Colors.white),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildTypingIndicator(bool isDark) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          CircleAvatar(
            radius: 16,
            backgroundColor: Theme.of(context).primaryColor.withOpacity(0.2),
            child: Icon(Icons.smart_toy, size: 18, color: Theme.of(context).primaryColor),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: isDark ? Colors.grey.shade800 : Colors.grey.shade100,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _buildDot(0),
                _buildDot(1),
                _buildDot(2),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDot(int index) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: Duration(milliseconds: 600 + index * 200),
      builder: (context, value, child) {
        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 2),
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: Colors.grey.withOpacity(0.4 + value * 0.3),
            shape: BoxShape.circle,
          ),
        );
      },
    );
  }

  void _sendQuickMessage(NegotiationPoint point) {
    _messageController.text = 'Tell me more about the ${point.category.replaceAll('_', ' ')} issue and how to negotiate it.';
    _sendMessage();
  }

  void _showNegotiationPoints() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.85,
        expand: false,
        builder: (context, scrollController) => Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                'Negotiation Points',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
              ),
            ),
            Expanded(
              child: ListView.builder(
                controller: scrollController,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: _negotiationPoints.length,
                itemBuilder: (context, i) {
                  final p = _negotiationPoints[i];
                  return Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(p.getSeverityIcon(), color: p.getSeverityColor(), size: 20),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  p.category.replaceAll('_', ' ').toUpperCase(),
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12,
                                    color: p.getSeverityColor(),
                                  ),
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(
                                  color: p.getSeverityColor().withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Text(
                                  p.severity.toUpperCase(),
                                  style: TextStyle(fontSize: 10, color: p.getSeverityColor(), fontWeight: FontWeight.bold),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Text(p.point, style: const TextStyle(fontSize: 14)),
                          if (p.strategy != null) ...[
                            const SizedBox(height: 8),
                            Container(
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: Colors.blue.shade50,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Icon(Icons.lightbulb, size: 16, color: Colors.blue.shade700),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      p.strategy!,
                                      style: TextStyle(fontSize: 12, color: Colors.blue.shade900),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
