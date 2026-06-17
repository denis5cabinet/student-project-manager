import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/comment.dart';
import 'comment_detail_screen.dart';

class CommentsScreen extends StatefulWidget {
  final int taskId;
  const CommentsScreen({super.key, required this.taskId});

  @override
  State<CommentsScreen> createState() => _CommentsScreenState();
}

class _CommentsScreenState extends State<CommentsScreen> {
  late Future<List<Comment>> futureComments;

  @override
  void initState() {
    super.initState();
    futureComments = ApiService().fetchComments(widget.taskId);
  }

  Future<void> _refresh() async {
    setState(() {
      futureComments = ApiService().fetchComments(widget.taskId);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Комментарии к задаче ${widget.taskId}')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<Comment>>(
          future: futureComments,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            } else if (snapshot.hasError) {
              return Center(child: Text('Ошибка: ${snapshot.error}'));
            } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
              return const Center(child: Text('Нет комментариев'));
            } else {
              final comments = snapshot.data!;
              return ListView.builder(
                itemCount: comments.length,
                itemBuilder: (context, index) {
                  final comment = comments[index];
                  return Card(
                    margin: const EdgeInsets.all(8),
                    child: ListTile(
                      title: Text(comment.content),
                      subtitle: Text('Автор: ${comment.authorId}'),
                      trailing: Text(comment.createdAt?.substring(0,10) ?? ''),
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => CommentDetailScreen(comment: comment),
                          ),
                        );
                      },
                    ),
                  );
                },
              );
            }
          },
        ),
      ),
    );
  }
}
