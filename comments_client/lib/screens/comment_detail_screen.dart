import 'package:flutter/material.dart';
import '../models/comment.dart';

class CommentDetailScreen extends StatelessWidget {
  final Comment comment;
  const CommentDetailScreen({super.key, required this.comment});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Комментарий #${comment.id}')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Текст:', style: TextStyle(fontWeight: FontWeight.bold)),
            Text(comment.content, style: TextStyle(fontSize: 18)),
            const SizedBox(height: 16),
            Text('Автор: ${comment.authorId}'),
            Text('Задача: ${comment.taskId}'),
            if (comment.parentCommentId != null)
              Text('Ответ на комментарий #${comment.parentCommentId}'),
            Text('Создан: ${comment.createdAt ?? 'неизвестно'}'),
            Text('Обновлён: ${comment.updatedAt ?? 'неизвестно'}'),
            Text('Удалён: ${comment.isDeleted ? 'да' : 'нет'}'),
          ],
        ),
      ),
    );
  }
}
