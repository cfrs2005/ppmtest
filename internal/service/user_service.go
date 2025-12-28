package service

import (
	"errors"

	"github.com/cfrs2005/ppmtest/internal/models"
	"github.com/cfrs2005/ppmtest/internal/repository"
)

var (
	ErrInvalidCredentials = errors.New("invalid credentials")
	ErrUserInactive       = errors.New("user is inactive")
	ErrUnauthorized       = errors.New("unauthorized access")
)

// UserService defines the interface for user business logic
type UserService interface {
	Register(user *models.User) error
	Login(email, password string) (*models.User, error)
	GetUserProfile(id uint) (*models.User, error)
	UpdateProfile(user *models.User) error
	DeleteUser(id uint, requesterID uint) error
	ListUsers(page, pageSize int) ([]*models.User, int64, error)
	ChangeStatus(id uint, status string) error
}

type userService struct {
	userRepo repository.UserRepository
}

// NewUserService creates a new user service
func NewUserService(userRepo repository.UserRepository) UserService {
	return &userService{
		userRepo: userRepo,
	}
}

func (s *userService) Register(user *models.User) error {
	existingUser, err := s.userRepo.FindByEmail(user.Email)
	if err == nil && existingUser != nil {
		return repository.ErrUserAlreadyExists
	}

	existingUser, err = s.userRepo.FindByUsername(user.Username)
	if err == nil && existingUser != nil {
		return repository.ErrUserAlreadyExists
	}

	user.Status = "active"
	user.Role = "author"

	return s.userRepo.Create(user)
}

func (s *userService) Login(email, password string) (*models.User, error) {
	user, err := s.userRepo.FindByEmail(email)
	if err != nil {
		if errors.Is(err, repository.ErrUserNotFound) {
			return nil, ErrInvalidCredentials
		}
		return nil, err
	}

	if user.Status != "active" {
		return nil, ErrUserInactive
	}

	if !comparePassword(user.Password, password) {
		return nil, ErrInvalidCredentials
	}

	return user, nil
}

func (s *userService) GetUserProfile(id uint) (*models.User, error) {
	return s.userRepo.FindByID(id)
}

func (s *userService) UpdateProfile(user *models.User) error {
	return s.userRepo.Update(user)
}

func (s *userService) DeleteUser(id uint, requesterID uint) error {
	requester, err := s.userRepo.FindByID(requesterID)
	if err != nil {
		return err
	}

	if requester.Role != "admin" && requesterID != id {
		return ErrUnauthorized
	}

	return s.userRepo.Delete(id)
}

func (s *userService) ListUsers(page, pageSize int) ([]*models.User, int64, error) {
	offset := (page - 1) * pageSize
	return s.userRepo.List(offset, pageSize)
}

func (s *userService) ChangeStatus(id uint, status string) error {
	user, err := s.userRepo.FindByID(id)
	if err != nil {
		return err
	}

	user.Status = status
	return s.userRepo.Update(user)
}

func comparePassword(hashedPassword, password string) bool {
	return hashedPassword == password
}