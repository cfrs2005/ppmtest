package service

import (
	"errors"
	"testing"

	"github.com/cfrs2005/ppmtest/internal/models"
	"github.com/cfrs2005/ppmtest/internal/repository"
)

type MockUserRepository struct {
	users map[uint]*models.User
}

func NewMockUserRepository() *MockUserRepository {
	return &MockUserRepository{
		users: make(map[uint]*models.User),
	}
}

func (m *MockUserRepository) Create(user *models.User) error {
	user.ID = uint(len(m.users) + 1)
	m.users[user.ID] = user
	return nil
}

func (m *MockUserRepository) FindByID(id uint) (*models.User, error) {
	user, ok := m.users[id]
	if !ok {
		return nil, repository.ErrUserNotFound
	}
	return user, nil
}

func (m *MockUserRepository) FindByEmail(email string) (*models.User, error) {
	for _, user := range m.users {
		if user.Email == email {
			return user, nil
		}
	}
	return nil, repository.ErrUserNotFound
}

func (m *MockUserRepository) FindByUsername(username string) (*models.User, error) {
	for _, user := range m.users {
		if user.Username == username {
			return user, nil
		}
	}
	return nil, repository.ErrUserNotFound
}

func (m *MockUserRepository) Update(user *models.User) error {
	if _, ok := m.users[user.ID]; !ok {
		return repository.ErrUserNotFound
	}
	m.users[user.ID] = user
	return nil
}

func (m *MockUserRepository) Delete(id uint) error {
	if _, ok := m.users[id]; !ok {
		return repository.ErrUserNotFound
	}
	delete(m.users, id)
	return nil
}

func (m *MockUserRepository) List(offset, limit int) ([]*models.User, int64, error) {
	users := make([]*models.User, 0, len(m.users))
	for _, user := range m.users {
		users = append(users, user)
	}
	return users, int64(len(users)), nil
}

func TestUserService_Register(t *testing.T) {
	tests := []struct {
		name    string
		user    *models.User
		wantErr error
	}{
		{
			name: "valid user",
			user: &models.User{
				Username: "testuser",
				Email:    "test@example.com",
				Password: "password123",
			},
			wantErr: nil,
		},
		{
			name: "empty email",
			user: &models.User{
				Username: "testuser",
				Email:    "",
				Password: "password123",
			},
			wantErr: nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockRepo := NewMockUserRepository()
			userService := NewUserService(mockRepo)

			err := userService.Register(tt.user)

			if tt.wantErr != nil && !errors.Is(err, tt.wantErr) {
				t.Errorf("Register() error = %v, wantErr %v", err, tt.wantErr)
			}

			if err == nil && tt.user.ID == 0 {
				t.Error("Register() did not set user ID")
			}
		})
	}
}

func TestUserService_Login(t *testing.T) {
	mockRepo := NewMockUserRepository()
	userService := NewUserService(mockRepo)

	user := &models.User{
		Username: "testuser",
		Email:    "test@example.com",
		Password: "password123",
		Status:   "active",
	}
	mockRepo.Create(user)

	tests := []struct {
		name    string
		email   string
		password string
		wantErr error
	}{
		{
			name:     "valid credentials",
			email:    "test@example.com",
			password: "password123",
			wantErr:  nil,
		},
		{
			name:     "invalid email",
			email:    "notfound@example.com",
			password: "password123",
			wantErr:  ErrInvalidCredentials,
		},
		{
			name:     "invalid password",
			email:    "test@example.com",
			password: "wrongpassword",
			wantErr:  ErrInvalidCredentials,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := userService.Login(tt.email, tt.password)

			if tt.wantErr != nil && !errors.Is(err, tt.wantErr) {
				t.Errorf("Login() error = %v, wantErr %v", err, tt.wantErr)
			}

			if tt.wantErr == nil && err != nil {
				t.Errorf("Login() unexpected error = %v", err)
			}
		})
	}
}