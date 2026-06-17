class Comment {
  final int id;
  final String content;
  final int authorId;
  final int taskId;
  final int? parentCommentId;
  final String? createdAt;
  final String? updatedAt;
  final bool isDeleted;

  Comment({
    required this.id,
    required this.content,
    required this.authorId,
    required this.taskId,
    this.parentCommentId,
    this.createdAt,
    this.updatedAt,
    this.isDeleted = false,
  });

  factory Comment.fromJson(Map<String, dynamic> json) {
    return Comment(
      id: json['id'],
      content: json['content'],
      authorId: json['author_id'],
      taskId: json['task_id'],
      parentCommentId: json['parent_comment_id'],
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
      isDeleted: json['is_deleted'] ?? false,
    );
  }
}
