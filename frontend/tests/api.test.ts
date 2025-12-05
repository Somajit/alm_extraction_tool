/**
 * Unit tests for authentication API service layer
 * 
 * Tests the new rationalized API methods in api.ts
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import { authApi } from '../src/api'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as any

describe('Authentication API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('authApi.authenticate', () => {
    it('should authenticate successfully', async () => {
      const mockResponse = {
        data: {
          success: true,
          message: 'Authenticated successfully',
          username: 'test_user'
        },
        status: 200
      }

      mockedAxios.create.mockReturnValue({
        post: vi.fn().mockResolvedValue(mockResponse)
      })

      const response = await authApi.authenticate('test_user', 'test_pass')

      expect(response.data.success).toBe(true)
      expect(response.data.username).toBe('test_user')
    })

    it('should handle authentication failure', async () => {
      const mockResponse = {
        data: {
          detail: 'Invalid credentials'
        },
        status: 500
      }

      mockedAxios.create.mockReturnValue({
        post: vi.fn().mockResolvedValue(mockResponse)
      })

      const response = await authApi.authenticate('test_user', 'wrong_pass')

      expect(response.status).toBe(500)
      expect(response.data.detail).toContain('Invalid credentials')
    })
  })

  describe('authApi.getDomains', () => {
    it('should fetch domains successfully', async () => {
      const mockResponse = {
        data: {
          success: true,
          domains: [
            { id: 'DEFAULT', name: 'Default Domain' },
            { id: 'CUSTOM', name: 'Custom Domain' }
          ]
        },
        status: 200
      }

      mockedAxios.create.mockReturnValue({
        get: vi.fn().mockResolvedValue(mockResponse)
      })

      const response = await authApi.getDomains('test_user')

      expect(response.data.success).toBe(true)
      expect(response.data.domains).toHaveLength(2)
      expect(response.data.domains[0].id).toBe('DEFAULT')
    })
  })

  describe('authApi.getProjects', () => {
    it('should fetch projects successfully', async () => {
      const mockResponse = {
        data: {
          success: true,
          projects: [
            { id: 'Project1', name: 'Project 1' },
            { id: 'Project2', name: 'Project 2' }
          ]
        },
        status: 200
      }

      mockedAxios.create.mockReturnValue({
        get: vi.fn().mockResolvedValue(mockResponse)
      })

      const response = await authApi.getProjects('test_user', 'DEFAULT')

      expect(response.data.success).toBe(true)
      expect(response.data.projects).toHaveLength(2)
      expect(response.data.projects[0].id).toBe('Project1')
    })
  })

  describe('authApi.login', () => {
    it('should complete login successfully', async () => {
      const mockResponse = {
        data: {
          success: true,
          testplan_root_folders: 5,
          testlab_releases: 3,
          defects: 150
        },
        status: 200
      }

      mockedAxios.create.mockReturnValue({
        post: vi.fn().mockResolvedValue(mockResponse)
      })

      const response = await authApi.login('test_user', 'DEFAULT', 'Project1')

      expect(response.data.success).toBe(true)
      expect(response.data.testplan_root_folders).toBe(5)
      expect(response.data.testlab_releases).toBe(3)
      expect(response.data.defects).toBe(150)
    })
  })

  describe('authApi.logout', () => {
    it('should logout successfully', async () => {
      const mockResponse = {
        data: {
          success: true,
          message: 'Logged out successfully'
        },
        status: 200
      }

      mockedAxios.create.mockReturnValue({
        post: vi.fn().mockResolvedValue(mockResponse)
      })

      const response = await authApi.logout('test_user')

      expect(response.data.success).toBe(true)
      expect(response.data.message).toBe('Logged out successfully')
    })
  })

  describe('Complete authentication flow', () => {
    it('should complete full flow: authenticate → getDomains → getProjects → login', async () => {
      // Mock all API calls
      const mockAxiosInstance = {
        post: vi.fn()
          .mockResolvedValueOnce({
            data: { success: true, message: 'Authenticated successfully', username: 'test_user' },
            status: 200
          })
          .mockResolvedValueOnce({
            data: { success: true, testplan_root_folders: 5, testlab_releases: 3, defects: 150 },
            status: 200
          }),
        get: vi.fn()
          .mockResolvedValueOnce({
            data: { success: true, domains: [{ id: 'DEFAULT', name: 'Default Domain' }] },
            status: 200
          })
          .mockResolvedValueOnce({
            data: { success: true, projects: [{ id: 'Project1', name: 'Project 1' }] },
            status: 200
          })
      }

      mockedAxios.create.mockReturnValue(mockAxiosInstance)

      // Step 1: Authenticate
      const authResponse = await authApi.authenticate('test_user', 'test_pass')
      expect(authResponse.data.success).toBe(true)

      // Step 2: Get domains
      const domainsResponse = await authApi.getDomains('test_user')
      expect(domainsResponse.data.success).toBe(true)
      expect(domainsResponse.data.domains).toHaveLength(1)

      // Step 3: Get projects
      const projectsResponse = await authApi.getProjects('test_user', 'DEFAULT')
      expect(projectsResponse.data.success).toBe(true)
      expect(projectsResponse.data.projects).toHaveLength(1)

      // Step 4: Login
      const loginResponse = await authApi.login('test_user', 'DEFAULT', 'Project1')
      expect(loginResponse.data.success).toBe(true)
      expect(loginResponse.data.testplan_root_folders).toBeGreaterThan(0)
    })
  })
})
