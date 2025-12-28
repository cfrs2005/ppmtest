package router

import (
	"github.com/cfrs2005/ppmtest/internal/handlers"
	"github.com/cfrs2005/ppmtest/internal/middleware"
	"github.com/cfrs2005/ppmtest/internal/service"
	"github.com/gin-gonic/gin"
)

func Setup(userService service.UserService, postService service.PostService) *gin.Engine {
	r := gin.New()

	r.Use(middleware.Logger())
	r.Use(middleware.Recovery())
	r.Use(middleware.CORS())

	userHandler := handlers.NewUserHandler(userService)
	postHandler := handlers.NewPostHandler(postService)

	api := r.Group("/api/v1")
	{
		auth := api.Group("/auth")
		{
			auth.POST("/register", userHandler.Register)
			auth.POST("/login", userHandler.Login)
		}

		users := api.Group("/users")
		{
			users.GET("/:id", userHandler.GetProfile)
			users.GET("", userHandler.ListUsers)
		}

		posts := api.Group("/posts")
		{
			posts.GET("", postHandler.ListPosts)
			posts.GET("/search", postHandler.SearchPosts)
			posts.GET("/:id", postHandler.GetPost)
			posts.GET("/slug/:slug", postHandler.GetPostBySlug)
			posts.POST("", postHandler.CreatePost)
			posts.PUT("/:id", postHandler.UpdatePost)
			posts.DELETE("/:id", postHandler.DeletePost)
			posts.POST("/:id/publish", postHandler.PublishPost)
		}
	}

	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok"})
	})

	return r
}