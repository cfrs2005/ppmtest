package router

import (
	"ppmtest/internal/handlers"
	"ppmtest/internal/middleware"

	"github.com/gin-gonic/gin"
)

func SetupRouter(
	userHandler *handlers.UserHandler,
	postHandler *handlers.PostHandler,
	commentHandler *handlers.CommentHandler,
) *gin.Engine {
	r := gin.Default()

	r.Use(middleware.CORSMiddleware())
	r.Use(middleware.LoggerMiddleware())

	api := r.Group("/api/v1")
	{
		auth := api.Group("/auth")
		{
			auth.POST("/register", userHandler.Register)
			auth.POST("/login", userHandler.Login)
		}

		users := api.Group("/users")
		{
			users.GET("", userHandler.List)
			users.GET("/:id", userHandler.GetByID)
			users.PUT("/:id", middleware.AuthMiddleware(), userHandler.Update)
			users.DELETE("/:id", middleware.AuthMiddleware(), userHandler.Delete)
		}

		posts := api.Group("/posts")
		{
			posts.GET("", postHandler.List)
			posts.GET("/:id", postHandler.GetByID)
			posts.GET("/slug/:slug", postHandler.GetBySlug)
			posts.GET("/search", postHandler.Search)

			posts.POST("", middleware.AuthMiddleware(), postHandler.Create)
			posts.PUT("/:id", middleware.AuthMiddleware(), postHandler.Update)
			posts.DELETE("/:id", middleware.AuthMiddleware(), postHandler.Delete)
			posts.POST("/:id/publish", middleware.AuthMiddleware(), postHandler.Publish)
		}

		comments := api.Group("/comments")
		{
			comments.GET("/:id", commentHandler.GetByID)
			comments.GET("/post/:post_id", commentHandler.GetByPostID)

			comments.POST("", middleware.AuthMiddleware(), commentHandler.Create)
			comments.PUT("/:id", middleware.AuthMiddleware(), commentHandler.Update)
			comments.DELETE("/:id", middleware.AuthMiddleware(), commentHandler.Delete)

			admin := comments.Group("/admin")
			admin.Use(middleware.AuthMiddleware(), middleware.RequireRole("admin"))
			{
				admin.POST("/:id/approve", commentHandler.Approve)
				admin.POST("/:id/reject", commentHandler.Reject)
				admin.POST("/:id/spam", commentHandler.MarkAsSpam)
			}
		}
	}

	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status": "ok",
		})
	})

	return r
}
