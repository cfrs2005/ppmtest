package container

import (
	"github.com/cfrs2005/ppmtest/internal/database"
	"github.com/cfrs2005/ppmtest/internal/repository"
	"github.com/cfrs2005/ppmtest/internal/service"
)

// Container holds all application dependencies
type Container struct {
	DB     *database.Database
	Users  service.UserService
	Posts  service.PostService
	Comments service.CommentService
}

// NewContainer creates a new dependency injection container
func NewContainer(db *database.Database) *Container {
	userRepo := repository.NewUserRepository(db.DB)
	postRepo := repository.NewPostRepository(db.DB)
	commentRepo := repository.NewCommentRepository(db.DB)
	tagRepo := repository.NewTagRepository(db.DB)
	categoryRepo := repository.NewCategoryRepository(db.DB)

	userService := service.NewUserService(userRepo)
	postService := service.NewPostService(postRepo, userRepo)
	commentService := service.NewCommentService(commentRepo, postRepo, userRepo)

	return &Container{
		DB:       db,
		Users:    userService,
		Posts:    postService,
		Comments: commentService,
	}
}