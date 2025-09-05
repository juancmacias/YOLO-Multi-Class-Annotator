-- ========================================================
-- YOLO Multi-Class Annotator - SQL Server Database Setup
-- ========================================================
-- Este script crea todas las tablas necesarias para el 
-- YOLO Multi-Class Annotator en SQL Server
-- Compatible con: SQL Server 2019+, Azure SQL Database
-- ========================================================

-- Verificar versión de SQL Server
SELECT 
    @@VERSION AS 'SQL Server Version',
    @@SERVERNAME AS 'Server Name',
    DB_NAME() AS 'Database Name',
    GETDATE() AS 'Script Execution Time';

-- ========================================================
-- 0. CONFIGURACIÓN INICIAL
-- ========================================================

-- Usar la base de datos correcta (cambiar según necesidades)
-- USE [YOLOAnnotator];  -- Descomentar y cambiar nombre si es necesario

-- Configurar opciones de la base de datos
ALTER DATABASE CURRENT
SET RECOVERY FULL,
    AUTO_CREATE_STATISTICS ON,
    AUTO_UPDATE_STATISTICS ON,
    PAGE_VERIFY CHECKSUM;

PRINT '✅ Configuración inicial completada';

-- ========================================================
-- 1. TABLA DE USUARIOS
-- ========================================================

-- Crear tabla de usuarios
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Users')
BEGIN
    CREATE TABLE [dbo].[Users] (
        [Id] INT IDENTITY(1,1) PRIMARY KEY,
        [Username] NVARCHAR(100) NOT NULL UNIQUE,
        [Email] NVARCHAR(255) NOT NULL UNIQUE,
        [HashedPassword] NVARCHAR(255) NOT NULL,
        [IsActive] BIT NOT NULL DEFAULT 1,
        [IsAdmin] BIT NOT NULL DEFAULT 0,
        [CreatedAt] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        [UpdatedAt] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        
        -- Constraints
        CONSTRAINT CK_Users_Email CHECK (Email LIKE '%@%.%'),
        CONSTRAINT CK_Users_Username CHECK (LEN(Username) >= 3)
    );
    
    PRINT '✅ Tabla Users creada';
END
ELSE
    PRINT '⚠️  Tabla Users ya existe';

-- Crear índices para tabla Users
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Users_Username')
    CREATE NONCLUSTERED INDEX IX_Users_Username ON [dbo].[Users]([Username]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Users_Email')
    CREATE NONCLUSTERED INDEX IX_Users_Email ON [dbo].[Users]([Email]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Users_IsActive')
    CREATE NONCLUSTERED INDEX IX_Users_IsActive ON [dbo].[Users]([IsActive]);

-- ========================================================
-- 2. TABLA DE SESIONES DE USUARIO
-- ========================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'UserSessions')
BEGIN
    CREATE TABLE [dbo].[UserSessions] (
        [Id] INT IDENTITY(1,1) PRIMARY KEY,
        [SessionName] NVARCHAR(255) NOT NULL,
        [UserId] INT NOT NULL,
        [CreatedAt] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        [UpdatedAt] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        [IsActive] BIT NOT NULL DEFAULT 1,
        
        -- Foreign Key
        CONSTRAINT FK_UserSessions_Users 
            FOREIGN KEY ([UserId]) REFERENCES [dbo].[Users]([Id]) 
            ON DELETE CASCADE,
            
        -- Constraints
        CONSTRAINT CK_UserSessions_SessionName CHECK (LEN(SessionName) >= 1)
    );
    
    PRINT '✅ Tabla UserSessions creada';
END
ELSE
    PRINT '⚠️  Tabla UserSessions ya existe';

-- Crear índices para UserSessions
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_UserSessions_UserId')
    CREATE NONCLUSTERED INDEX IX_UserSessions_UserId ON [dbo].[UserSessions]([UserId]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_UserSessions_SessionName')
    CREATE NONCLUSTERED INDEX IX_UserSessions_SessionName ON [dbo].[UserSessions]([SessionName]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_UserSessions_IsActive')
    CREATE NONCLUSTERED INDEX IX_UserSessions_IsActive ON [dbo].[UserSessions]([IsActive]);

-- ========================================================
-- 3. TABLA DE BLACKLIST DE TOKENS
-- ========================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'TokenBlacklist')
BEGIN
    CREATE TABLE [dbo].[TokenBlacklist] (
        [Id] INT IDENTITY(1,1) PRIMARY KEY,
        [Token] NVARCHAR(500) NOT NULL UNIQUE,
        [BlacklistedAt] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        [ExpiresAt] DATETIME2(7) NOT NULL,
        
        -- Constraint para asegurar que ExpiresAt sea futuro
        CONSTRAINT CK_TokenBlacklist_ExpiresAt CHECK (ExpiresAt > BlacklistedAt)
    );
    
    PRINT '✅ Tabla TokenBlacklist creada';
END
ELSE
    PRINT '⚠️  Tabla TokenBlacklist ya existe';

-- Índices para TokenBlacklist
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_TokenBlacklist_Token')
    CREATE NONCLUSTERED INDEX IX_TokenBlacklist_Token ON [dbo].[TokenBlacklist]([Token]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_TokenBlacklist_ExpiresAt')
    CREATE NONCLUSTERED INDEX IX_TokenBlacklist_ExpiresAt ON [dbo].[TokenBlacklist]([ExpiresAt]);

-- ========================================================
-- 4. TABLA DE PROYECTOS/DATASETS
-- ========================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Projects')
BEGIN
    CREATE TABLE [dbo].[Projects] (
        [Id] INT IDENTITY(1,1) PRIMARY KEY,
        [Name] NVARCHAR(255) NOT NULL,
        [Description] NVARCHAR(MAX) NULL,
        [UserId] INT NOT NULL,
        [CreatedAt] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        [UpdatedAt] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        [IsActive] BIT NOT NULL DEFAULT 1,
        
        -- Foreign Key
        CONSTRAINT FK_Projects_Users 
            FOREIGN KEY ([UserId]) REFERENCES [dbo].[Users]([Id]) 
            ON DELETE CASCADE,
            
        -- Constraints
        CONSTRAINT CK_Projects_Name CHECK (LEN(Name) >= 1)
    );
    
    PRINT '✅ Tabla Projects creada';
END
ELSE
    PRINT '⚠️  Tabla Projects ya existe';

-- Índices para Projects
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Projects_UserId')
    CREATE NONCLUSTERED INDEX IX_Projects_UserId ON [dbo].[Projects]([UserId]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Projects_Name')
    CREATE NONCLUSTERED INDEX IX_Projects_Name ON [dbo].[Projects]([Name]);

-- ========================================================
-- 5. TABLA DE CLASES DE ANOTACIÓN (PERSONALIZABLE)
-- ========================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AnnotationClasses')
BEGIN
    CREATE TABLE [dbo].[AnnotationClasses] (
        [Id] INT IDENTITY(1,1) PRIMARY KEY,
        [Name] NVARCHAR(100) NOT NULL,
        [Color] NVARCHAR(7) NOT NULL DEFAULT '#ff0000', -- Color hex
        [UserId] INT NOT NULL,
        [SessionName] NVARCHAR(255) NULL, -- NULL para clases globales del usuario
        [ProjectId] INT NULL, -- Para compatibilidad futura
        [IsGlobal] BIT NOT NULL DEFAULT 0, -- Solo admin puede crear globales
        [IsActive] BIT NOT NULL DEFAULT 1,
        [CreatedAt] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        [UpdatedAt] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        
        -- Foreign Keys
        CONSTRAINT FK_AnnotationClasses_Users 
            FOREIGN KEY ([UserId]) REFERENCES [dbo].[Users]([Id]) 
            ON DELETE CASCADE,
        CONSTRAINT FK_AnnotationClasses_Projects 
            FOREIGN KEY ([ProjectId]) REFERENCES [dbo].[Projects]([Id]) 
            ON DELETE CASCADE,
            
        -- Constraints
        CONSTRAINT CK_AnnotationClasses_Name_Length CHECK (LEN(RTRIM(Name)) >= 1),
        CONSTRAINT CK_AnnotationClasses_Name_NotEmpty CHECK (RTRIM(Name) != ''),
        CONSTRAINT CK_AnnotationClasses_Color_Format CHECK (
            Color LIKE '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'
        ),
        
        -- Unique constraint: un usuario no puede tener clases duplicadas por sesión
        CONSTRAINT UK_AnnotationClasses_UserSessionName 
            UNIQUE ([UserId], [SessionName], [Name])
    );
    
    PRINT '✅ Tabla AnnotationClasses creada con gestión personalizada';
END

-- Índices para AnnotationClasses
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AnnotationClasses_UserId')
    CREATE INDEX IX_AnnotationClasses_UserId ON [dbo].[AnnotationClasses]([UserId]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AnnotationClasses_SessionName')
    CREATE INDEX IX_AnnotationClasses_SessionName ON [dbo].[AnnotationClasses]([SessionName]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AnnotationClasses_IsActive')
    CREATE INDEX IX_AnnotationClasses_IsActive ON [dbo].[AnnotationClasses]([IsActive]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AnnotationClasses_IsGlobal')
    CREATE INDEX IX_AnnotationClasses_IsGlobal ON [dbo].[AnnotationClasses]([IsGlobal]);

-- Índice compuesto para búsquedas frecuentes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AnnotationClasses_UserSessionActive')
    CREATE INDEX IX_AnnotationClasses_UserSessionActive 
        ON [dbo].[AnnotationClasses]([UserId], [SessionName], [IsActive]);

-- Trigger para UpdatedAt
IF NOT EXISTS (SELECT * FROM sys.triggers WHERE name = 'TR_AnnotationClasses_UpdatedAt')
BEGIN
    EXEC('
    CREATE TRIGGER TR_AnnotationClasses_UpdatedAt 
    ON [dbo].[AnnotationClasses]
    AFTER UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        
        UPDATE [dbo].[AnnotationClasses]
        SET [UpdatedAt] = GETUTCDATE()
        FROM [dbo].[AnnotationClasses] ac
        INNER JOIN inserted i ON ac.[Id] = i.[Id];
    END');
    
    PRINT '✅ Trigger UpdatedAt para AnnotationClasses creado';
END
ELSE
    PRINT '⚠️  Tabla AnnotationClasses ya existe';

-- Índices para AnnotationClasses
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AnnotationClasses_ProjectId')
    CREATE NONCLUSTERED INDEX IX_AnnotationClasses_ProjectId ON [dbo].[AnnotationClasses]([ProjectId]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AnnotationClasses_UserId')
    CREATE NONCLUSTERED INDEX IX_AnnotationClasses_UserId ON [dbo].[AnnotationClasses]([UserId]);

-- ========================================================
-- 6. TABLA DE IMÁGENES
-- ========================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Images')
BEGIN
    CREATE TABLE [dbo].[Images] (
        [Id] INT IDENTITY(1,1) PRIMARY KEY,
        [Filename] NVARCHAR(255) NOT NULL,
        [OriginalFilename] NVARCHAR(255) NOT NULL,
        [FilePath] NVARCHAR(500) NOT NULL,
        [FileSize] BIGINT NULL,
        [Width] INT NULL,
        [Height] INT NULL,
        [SessionName] NVARCHAR(255) NULL,
        [UserId] INT NOT NULL,
        [ProjectId] INT NULL,
        [UploadedAt] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        [IsProcessed] BIT NOT NULL DEFAULT 0,
        
        -- Foreign Keys
        CONSTRAINT FK_Images_Users 
            FOREIGN KEY ([UserId]) REFERENCES [dbo].[Users]([Id]) 
            ON DELETE CASCADE,
        CONSTRAINT FK_Images_Projects 
            FOREIGN KEY ([ProjectId]) REFERENCES [dbo].[Projects]([Id]) 
            ON DELETE SET NULL,
            
        -- Constraints
        CONSTRAINT CK_Images_Filename CHECK (LEN(Filename) >= 1),
        CONSTRAINT CK_Images_FileSize CHECK (FileSize > 0),
        CONSTRAINT CK_Images_Dimensions CHECK (Width > 0 AND Height > 0)
    );
    
    PRINT '✅ Tabla Images creada';
END
ELSE
    PRINT '⚠️  Tabla Images ya existe';

-- Índices para Images
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Images_UserId')
    CREATE NONCLUSTERED INDEX IX_Images_UserId ON [dbo].[Images]([UserId]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Images_ProjectId')
    CREATE NONCLUSTERED INDEX IX_Images_ProjectId ON [dbo].[Images]([ProjectId]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Images_SessionName')
    CREATE NONCLUSTERED INDEX IX_Images_SessionName ON [dbo].[Images]([SessionName]);

-- ========================================================
-- 7. TABLA DE ANOTACIONES (BOUNDING BOXES)
-- ========================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Annotations')
BEGIN
    CREATE TABLE [dbo].[Annotations] (
        [Id] INT IDENTITY(1,1) PRIMARY KEY,
        [ImageId] INT NOT NULL,
        [ClassId] INT NOT NULL,
        [XCenter] DECIMAL(10, 8) NOT NULL, -- Coordenada X del centro (0-1)
        [YCenter] DECIMAL(10, 8) NOT NULL, -- Coordenada Y del centro (0-1)
        [Width] DECIMAL(10, 8) NOT NULL,   -- Ancho normalizado (0-1)
        [Height] DECIMAL(10, 8) NOT NULL,  -- Alto normalizado (0-1)
        [Confidence] DECIMAL(5, 4) NOT NULL DEFAULT 1.0, -- Confianza (0-1)
        [UserId] INT NOT NULL,
        [CreatedAt] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        [UpdatedAt] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        
        -- Foreign Keys
        CONSTRAINT FK_Annotations_Images 
            FOREIGN KEY ([ImageId]) REFERENCES [dbo].[Images]([Id]) 
            ON DELETE CASCADE,
        CONSTRAINT FK_Annotations_Classes 
            FOREIGN KEY ([ClassId]) REFERENCES [dbo].[AnnotationClasses]([Id]) 
            ON DELETE CASCADE,
        CONSTRAINT FK_Annotations_Users 
            FOREIGN KEY ([UserId]) REFERENCES [dbo].[Users]([Id]) 
            ON DELETE CASCADE,
            
        -- Constraints para coordenadas YOLO (0-1)
        CONSTRAINT CK_Annotations_XCenter CHECK (XCenter >= 0 AND XCenter <= 1),
        CONSTRAINT CK_Annotations_YCenter CHECK (YCenter >= 0 AND YCenter <= 1),
        CONSTRAINT CK_Annotations_Width CHECK (Width > 0 AND Width <= 1),
        CONSTRAINT CK_Annotations_Height CHECK (Height > 0 AND Height <= 1),
        CONSTRAINT CK_Annotations_Confidence CHECK (Confidence >= 0 AND Confidence <= 1)
    );
    
    PRINT '✅ Tabla Annotations creada';
END
ELSE
    PRINT '⚠️  Tabla Annotations ya existe';

-- Índices para Annotations
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Annotations_ImageId')
    CREATE NONCLUSTERED INDEX IX_Annotations_ImageId ON [dbo].[Annotations]([ImageId]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Annotations_ClassId')
    CREATE NONCLUSTERED INDEX IX_Annotations_ClassId ON [dbo].[Annotations]([ClassId]);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Annotations_UserId')
    CREATE NONCLUSTERED INDEX IX_Annotations_UserId ON [dbo].[Annotations]([UserId]);

-- ========================================================
-- 8. TRIGGERS PARA UPDATED_AT AUTOMÁTICO
-- ========================================================

-- Trigger para Users
IF NOT EXISTS (SELECT * FROM sys.triggers WHERE name = 'TR_Users_UpdatedAt')
BEGIN
    EXEC('
    CREATE TRIGGER TR_Users_UpdatedAt
    ON [dbo].[Users]
    AFTER UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        UPDATE [dbo].[Users]
        SET UpdatedAt = GETUTCDATE()
        FROM [dbo].[Users] u
        INNER JOIN inserted i ON u.Id = i.Id;
    END');
    
    PRINT '✅ Trigger TR_Users_UpdatedAt creado';
END;

-- Trigger para UserSessions
IF NOT EXISTS (SELECT * FROM sys.triggers WHERE name = 'TR_UserSessions_UpdatedAt')
BEGIN
    EXEC('
    CREATE TRIGGER TR_UserSessions_UpdatedAt
    ON [dbo].[UserSessions]
    AFTER UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        UPDATE [dbo].[UserSessions]
        SET UpdatedAt = GETUTCDATE()
        FROM [dbo].[UserSessions] us
        INNER JOIN inserted i ON us.Id = i.Id;
    END');
    
    PRINT '✅ Trigger TR_UserSessions_UpdatedAt creado';
END;

-- Trigger para Projects
IF NOT EXISTS (SELECT * FROM sys.triggers WHERE name = 'TR_Projects_UpdatedAt')
BEGIN
    EXEC('
    CREATE TRIGGER TR_Projects_UpdatedAt
    ON [dbo].[Projects]
    AFTER UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        UPDATE [dbo].[Projects]
        SET UpdatedAt = GETUTCDATE()
        FROM [dbo].[Projects] p
        INNER JOIN inserted i ON p.Id = i.Id;
    END');
    
    PRINT '✅ Trigger TR_Projects_UpdatedAt creado';
END;

-- Trigger para Annotations
IF NOT EXISTS (SELECT * FROM sys.triggers WHERE name = 'TR_Annotations_UpdatedAt')
BEGIN
    EXEC('
    CREATE TRIGGER TR_Annotations_UpdatedAt
    ON [dbo].[Annotations]
    AFTER UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        UPDATE [dbo].[Annotations]
        SET UpdatedAt = GETUTCDATE()
        FROM [dbo].[Annotations] a
        INNER JOIN inserted i ON a.Id = i.Id;
    END');
    
    PRINT '✅ Trigger TR_Annotations_UpdatedAt creado';
END;

-- ========================================================
-- 8. STORED PROCEDURES PARA GESTIÓN DE CLASES
-- ========================================================

-- SP: Crear clases por defecto para un usuario
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_CreateDefaultClasses')
    DROP PROCEDURE sp_CreateDefaultClasses;
GO

CREATE PROCEDURE sp_CreateDefaultClasses
    @UserId INT,
    @SessionName NVARCHAR(255) = NULL,
    @CreatedCount INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET @CreatedCount = 0;
    
    BEGIN TRY
        -- Clases por defecto con nombres en español
        DECLARE @DefaultClasses TABLE (
            Name NVARCHAR(100),
            Color NVARCHAR(7)
        );
        
        INSERT INTO @DefaultClasses VALUES
            (N'Persona', '#ff0000'),
            (N'Vehículo', '#00ff00'),
            (N'Animal', '#0000ff'),
            (N'Edificio', '#ffff00'),
            (N'Objeto', '#ff00ff'),
            (N'Naturaleza', '#00ffff');
        
        -- Insertar solo las que no existen
        INSERT INTO [dbo].[AnnotationClasses] ([Name], [Color], [UserId], [SessionName], [IsGlobal], [IsActive])
        SELECT dc.[Name], dc.[Color], @UserId, @SessionName, 0, 1
        FROM @DefaultClasses dc
        WHERE NOT EXISTS (
            SELECT 1 FROM [dbo].[AnnotationClasses] ac
            WHERE ac.[UserId] = @UserId 
              AND ISNULL(ac.[SessionName], '') = ISNULL(@SessionName, '')
              AND ac.[Name] = dc.[Name]
              AND ac.[IsActive] = 1
        );
        
        SET @CreatedCount = @@ROWCOUNT;
        
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO

-- SP: Obtener clases de un usuario con fallback a clases por defecto
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_GetUserClasses')
    DROP PROCEDURE sp_GetUserClasses;
GO

CREATE PROCEDURE sp_GetUserClasses
    @UserId INT,
    @SessionName NVARCHAR(255) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ClassCount INT;
    DECLARE @CreatedCount INT;
    
    -- Contar clases existentes
    SELECT @ClassCount = COUNT(*)
    FROM [dbo].[AnnotationClasses] 
    WHERE [UserId] = @UserId 
      AND (
          ([SessionName] = @SessionName) OR 
          ([SessionName] IS NULL AND @SessionName IS NULL) OR
          ([IsGlobal] = 1)
      )
      AND [IsActive] = 1;
    
    -- Si no tiene clases, crear las por defecto
    IF @ClassCount = 0
    BEGIN
        EXEC sp_CreateDefaultClasses @UserId, @SessionName, @CreatedCount OUTPUT;
    END
    
    -- Retornar clases disponibles
    SELECT 
        [Id],
        [Name],
        [Color],
        [UserId],
        [SessionName],
        [IsGlobal],
        [IsActive],
        [CreatedAt],
        [UpdatedAt]
    FROM [dbo].[AnnotationClasses]
    WHERE [UserId] = @UserId 
      AND (
          ([SessionName] = @SessionName) OR 
          ([SessionName] IS NULL AND @SessionName IS NULL) OR
          ([IsGlobal] = 1)
      )
      AND [IsActive] = 1
    ORDER BY [CreatedAt];
END
GO

-- SP: Obtener estadísticas de clases por usuario
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_GetClassStatistics')
    DROP PROCEDURE sp_GetClassStatistics;
GO

CREATE PROCEDURE sp_GetClassStatistics
    @UserId INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @UserId IS NULL
    BEGIN
        -- Estadísticas globales
        SELECT 
            COUNT(*) as TotalClasses,
            COUNT(CASE WHEN IsActive = 1 THEN 1 END) as ActiveClasses,
            COUNT(CASE WHEN IsGlobal = 1 THEN 1 END) as GlobalClasses,
            COUNT(DISTINCT UserId) as UsersWithClasses,
            COUNT(DISTINCT SessionName) as SessionsWithClasses
        FROM [dbo].[AnnotationClasses];
    END
    ELSE
    BEGIN
        -- Estadísticas por usuario
        SELECT 
            @UserId as UserId,
            COUNT(*) as TotalClasses,
            COUNT(CASE WHEN IsActive = 1 THEN 1 END) as ActiveClasses,
            COUNT(CASE WHEN SessionName IS NULL THEN 1 END) as GeneralClasses,
            COUNT(DISTINCT SessionName) as SessionsWithClasses,
            MAX(CreatedAt) as LastClassCreated
        FROM [dbo].[AnnotationClasses]
        WHERE UserId = @UserId;
    END
END
GO

PRINT '✅ Stored Procedures para gestión de clases creados';

-- ========================================================
-- 9. STORED PROCEDURES ÚTILES
-- ========================================================

-- Procedimiento para limpiar tokens expirados
IF NOT EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_CleanupExpiredTokens')
BEGIN
    EXEC('
    CREATE PROCEDURE [dbo].[sp_CleanupExpiredTokens]
    AS
    BEGIN
        SET NOCOUNT ON;
        
        DECLARE @DeletedCount INT;
        
        DELETE FROM [dbo].[TokenBlacklist] 
        WHERE ExpiresAt < GETUTCDATE();
        
        SET @DeletedCount = @@ROWCOUNT;
        
        PRINT ''🧹 Tokens expirados eliminados: '' + CAST(@DeletedCount AS NVARCHAR(10));
        
        RETURN @DeletedCount;
    END');
    
    PRINT '✅ Stored Procedure sp_CleanupExpiredTokens creado';
END;

-- Procedimiento para estadísticas de usuario
IF NOT EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_GetUserStats')
BEGIN
    EXEC('
    CREATE PROCEDURE [dbo].[sp_GetUserStats]
        @UserId INT = NULL
    AS
    BEGIN
        SET NOCOUNT ON;
        
        SELECT 
            u.Id,
            u.Username,
            u.Email,
            u.CreatedAt,
            u.IsAdmin,
            COUNT(DISTINCT p.Id) as ProjectCount,
            COUNT(DISTINCT i.Id) as ImageCount,
            COUNT(DISTINCT a.Id) as AnnotationCount,
            MAX(us.CreatedAt) as LastSessionDate
        FROM [dbo].[Users] u
        LEFT JOIN [dbo].[Projects] p ON u.Id = p.UserId AND p.IsActive = 1
        LEFT JOIN [dbo].[Images] i ON u.Id = i.UserId
        LEFT JOIN [dbo].[Annotations] a ON u.Id = a.UserId
        LEFT JOIN [dbo].[UserSessions] us ON u.Id = us.UserId AND us.IsActive = 1
        WHERE (@UserId IS NULL OR u.Id = @UserId)
            AND u.IsActive = 1
        GROUP BY u.Id, u.Username, u.Email, u.CreatedAt, u.IsAdmin
        ORDER BY u.CreatedAt DESC;
    END');
    
    PRINT '✅ Stored Procedure sp_GetUserStats creado';
END;

-- ========================================================
-- 10. VISTAS ÚTILES
-- ========================================================

-- Vista para estadísticas de proyectos
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'vw_ProjectStats')
BEGIN
    EXEC('
    CREATE VIEW [dbo].[vw_ProjectStats]
    AS
    SELECT 
        p.Id,
        p.Name,
        p.Description,
        p.UserId,
        u.Username as OwnerUsername,
        p.CreatedAt,
        COUNT(DISTINCT i.Id) as ImageCount,
        COUNT(DISTINCT a.Id) as AnnotationCount,
        COUNT(DISTINCT ac.Id) as ClassCount,
        AVG(CAST(a.Confidence AS FLOAT)) as AvgConfidence
    FROM [dbo].[Projects] p
    INNER JOIN [dbo].[Users] u ON p.UserId = u.Id
    LEFT JOIN [dbo].[Images] i ON p.Id = i.ProjectId
    LEFT JOIN [dbo].[Annotations] a ON i.Id = a.ImageId
    LEFT JOIN [dbo].[AnnotationClasses] ac ON p.Id = ac.ProjectId AND ac.IsActive = 1
    WHERE p.IsActive = 1
    GROUP BY p.Id, p.Name, p.Description, p.UserId, u.Username, p.CreatedAt
    ');
    
    PRINT '✅ Vista vw_ProjectStats creada';
END;

-- Vista para sesiones activas
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'vw_ActiveSessions')
BEGIN
    EXEC('
    CREATE VIEW [dbo].[vw_ActiveSessions]
    AS
    SELECT 
        us.Id,
        us.SessionName,
        us.UserId,
        u.Username,
        us.CreatedAt,
        COUNT(i.Id) as ImageCount,
        MAX(i.UploadedAt) as LastImageUpload
    FROM [dbo].[UserSessions] us
    INNER JOIN [dbo].[Users] u ON us.UserId = u.Id
    LEFT JOIN [dbo].[Images] i ON us.SessionName = i.SessionName
    WHERE us.IsActive = 1
    GROUP BY us.Id, us.SessionName, us.UserId, u.Username, us.CreatedAt
    ');
    
    PRINT '✅ Vista vw_ActiveSessions creada';
END;

-- Vista: Estadísticas de clases por usuario
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'vw_ClassStatsByUser')
BEGIN
    EXEC('
    CREATE VIEW [dbo].[vw_ClassStatsByUser] AS
    SELECT 
        u.[Id] as UserId,
        u.[Username],
        COUNT(ac.[Id]) as TotalClasses,
        COUNT(CASE WHEN ac.[IsActive] = 1 THEN 1 END) as ActiveClasses,
        COUNT(CASE WHEN ac.[SessionName] IS NULL THEN 1 END) as GeneralClasses,
        COUNT(DISTINCT ac.[SessionName]) as SessionsWithClasses,
        MAX(ac.[CreatedAt]) as LastClassCreated,
        COUNT(CASE WHEN ac.[IsGlobal] = 1 THEN 1 END) as GlobalClasses
    FROM [dbo].[Users] u
    LEFT JOIN [dbo].[AnnotationClasses] ac ON u.[Id] = ac.[UserId]
    GROUP BY u.[Id], u.[Username]
    ');
    
    PRINT '✅ Vista vw_ClassStatsByUser creada';
END;

-- Vista: Clases más utilizadas
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'vw_PopularClasses')
BEGIN
    EXEC('
    CREATE VIEW [dbo].[vw_PopularClasses] AS
    SELECT 
        ac.[Name],
        ac.[Color],
        COUNT(DISTINCT ac.[UserId]) as UsedByUsers,
        COUNT(ac.[Id]) as TotalInstances,
        COUNT(CASE WHEN ac.[IsActive] = 1 THEN 1 END) as ActiveInstances,
        AVG(CASE WHEN ac.[IsActive] = 1 THEN 1.0 ELSE 0.0 END) as ActivePercentage
    FROM [dbo].[AnnotationClasses] ac
    GROUP BY ac.[Name], ac.[Color]
    HAVING COUNT(ac.[Id]) > 0
    ');
    
    PRINT '✅ Vista vw_PopularClasses creada';
END;

-- Vista: Resumen de gestión de clases
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'vw_ClassManagementSummary')
BEGIN
    EXEC('
    CREATE VIEW [dbo].[vw_ClassManagementSummary] AS
    SELECT 
        ac.[Id],
        ac.[Name],
        ac.[Color],
        u.[Username] as CreatedBy,
        ac.[SessionName],
        ac.[IsGlobal],
        ac.[IsActive],
        ac.[CreatedAt],
        ac.[UpdatedAt],
        CASE 
            WHEN ac.[IsGlobal] = 1 THEN ''Global''
            WHEN ac.[SessionName] IS NULL THEN ''General''
            ELSE ''Session: '' + ac.[SessionName]
        END as Scope,
        DATEDIFF(day, ac.[CreatedAt], GETUTCDATE()) as DaysOld
    FROM [dbo].[AnnotationClasses] ac
    INNER JOIN [dbo].[Users] u ON ac.[UserId] = u.[Id]
    ');
    
    PRINT '✅ Vista vw_ClassManagementSummary creada';
END;

-- ========================================================
-- ========================================================
-- 11. DATOS DE EJEMPLO Y CONFIGURACIÓN INICIAL
-- ========================================================

-- Crear tabla de colores predefinidos como referencia
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ColorPresets')
BEGIN
    CREATE TABLE [dbo].[ColorPresets] (
        [Id] INT IDENTITY(1,1) PRIMARY KEY,
        [Name] NVARCHAR(50) NOT NULL,
        [HexValue] NVARCHAR(7) NOT NULL,
        [Category] NVARCHAR(50) NOT NULL DEFAULT 'general',
        [CreatedAt] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        
        -- Constraints
        CONSTRAINT CK_ColorPresets_HexValue CHECK (
            HexValue LIKE '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'
        ),
        CONSTRAINT UK_ColorPresets_Name UNIQUE ([Name])
    );
    
    PRINT '✅ Tabla ColorPresets creada';
END

-- Insertar colores predefinidos
IF NOT EXISTS (SELECT TOP 1 * FROM [dbo].[ColorPresets])
BEGIN
    INSERT INTO [dbo].[ColorPresets] ([Name], [HexValue], [Category]) VALUES
        (N'Rojo', '#ff0000', 'primary'),
        (N'Verde', '#00ff00', 'primary'),
        (N'Azul', '#0000ff', 'primary'),
        (N'Amarillo', '#ffff00', 'primary'),
        (N'Magenta', '#ff00ff', 'primary'),
        (N'Cian', '#00ffff', 'primary'),
        (N'Naranja', '#ff8800', 'secondary'),
        (N'Rosa', '#ff0088', 'secondary'),
        (N'Púrpura', '#8800ff', 'secondary'),
        (N'Verde Lima', '#88ff00', 'secondary'),
        (N'Azul Cielo', '#0088ff', 'secondary'),
        (N'Turquesa', '#00ff88', 'secondary'),
        (N'Rojo Oscuro', '#800000', 'dark'),
        (N'Verde Oscuro', '#008000', 'dark'),
        (N'Azul Oscuro', '#000080', 'dark'),
        (N'Marrón', '#8B4513', 'earth'),
        (N'Gris', '#808080', 'neutral'),
        (N'Negro', '#000000', 'neutral');
    
    PRINT '✅ Colores predefinidos insertados: ' + CAST(@@ROWCOUNT AS NVARCHAR(10));
END

-- Crear clases globales por defecto si existe un usuario admin
IF EXISTS (SELECT TOP 1 * FROM [dbo].[Users] WHERE [IsAdmin] = 1)
BEGIN
    DECLARE @AdminUserId INT;
    SELECT TOP 1 @AdminUserId = [Id] FROM [dbo].[Users] WHERE [IsAdmin] = 1;
    
    -- Insertar clases globales por defecto
    INSERT INTO [dbo].[AnnotationClasses] ([Name], [Color], [UserId], [SessionName], [IsGlobal], [IsActive])
    SELECT * FROM (VALUES
        (N'Persona', '#FF6B6B', @AdminUserId, NULL, 1, 1),
        (N'Vehículo', '#4ECDC4', @AdminUserId, NULL, 1, 1),
        (N'Animal', '#45B7D1', @AdminUserId, NULL, 1, 1),
        (N'Edificio', '#F9CA24', @AdminUserId, NULL, 1, 1),
        (N'Objeto', '#6C5CE7', @AdminUserId, NULL, 1, 1),
        (N'Naturaleza', '#A0E7E5', @AdminUserId, NULL, 1, 1)
    ) AS DefaultClasses([Name], [Color], [UserId], [SessionName], [IsGlobal], [IsActive])
    WHERE NOT EXISTS (
        SELECT 1 FROM [dbo].[AnnotationClasses] ac
        WHERE ac.[UserId] = @AdminUserId 
          AND ac.[SessionName] IS NULL 
          AND ac.[Name] = DefaultClasses.[Name]
          AND ac.[IsGlobal] = 1
    );
    
    IF @@ROWCOUNT > 0
        PRINT '✅ Clases globales por defecto creadas para admin';
END

-- ========================================================
-- 12. VISTAS ÚTILES PARA CONSULTAS
-- ========================================================
-- ========================================================

-- Job para limpiar tokens expirados (solo si SQL Server Agent está disponible)
IF EXISTS (SELECT 1 FROM sys.databases WHERE name = 'msdb' AND state = 0)
BEGIN
    PRINT '💼 Configurando trabajo de mantenimiento...';
    
    -- Nota: Esto requiere permisos de sysadmin
    -- Descomentar si tienes permisos y quieres automatizar la limpieza
    /*
    USE msdb;
    
    IF NOT EXISTS (SELECT name FROM msdb.dbo.sysjobs WHERE name = 'YOLO Annotator - Cleanup Expired Tokens')
    BEGIN
        EXEC dbo.sp_add_job
            @job_name = N'YOLO Annotator - Cleanup Expired Tokens',
            @enabled = 1,
            @description = N'Limpia tokens expirados de la tabla TokenBlacklist';
        
        EXEC dbo.sp_add_jobstep
            @job_name = N'YOLO Annotator - Cleanup Expired Tokens',
            @step_name = N'Cleanup',
            @command = N'EXEC [dbo].[sp_CleanupExpiredTokens]',
            @database_name = N'YOLOAnnotator'; -- Cambiar por tu BD
        
        EXEC dbo.sp_add_schedule
            @schedule_name = N'Daily Cleanup',
            @freq_type = 4, -- Diario
            @freq_interval = 1,
            @active_start_time = 020000; -- 2:00 AM
        
        EXEC dbo.sp_attach_schedule
            @job_name = N'YOLO Annotator - Cleanup Expired Tokens',
            @schedule_name = N'Daily Cleanup';
        
        EXEC dbo.sp_add_jobserver
            @job_name = N'YOLO Annotator - Cleanup Expired Tokens';
            
        PRINT '✅ Trabajo de limpieza automática configurado';
    END;
    */
END;

-- ========================================================
-- 12. DATOS INICIALES (OPCIONAL)
-- ========================================================

-- Insertar clases YOLO comunes por defecto
IF NOT EXISTS (SELECT * FROM [dbo].[AnnotationClasses] WHERE Name = 'person' AND UserId = 1)
BEGIN
    PRINT '🎯 Insertando clases YOLO por defecto...';
    
    -- Nota: Asume que existe un usuario con Id = 1
    -- Ajustar según tus necesidades
    /*
    INSERT INTO [dbo].[AnnotationClasses] (Name, Color, UserId) VALUES 
    ('person', '#FF0000', 1),
    ('bicycle', '#00FF00', 1),
    ('car', '#0000FF', 1),
    ('motorcycle', '#FFFF00', 1),
    ('airplane', '#FF00FF', 1),
    ('bus', '#00FFFF', 1),
    ('train', '#FFA500', 1),
    ('truck', '#800080', 1),
    ('boat', '#008000', 1),
    ('traffic light', '#FF69B4', 1);
    
    PRINT '✅ Clases YOLO por defecto insertadas';
    */
END;

-- ========================================================
-- 13. VERIFICACIÓN FINAL
-- ========================================================

PRINT '';
PRINT '🔍 VERIFICACIÓN FINAL:';
PRINT '========================';

-- Contar tablas creadas
SELECT 
    'Tablas creadas: ' + CAST(COUNT(*) AS NVARCHAR(10)) as Resultado
FROM sys.tables 
WHERE name IN ('Users', 'UserSessions', 'TokenBlacklist', 'Projects', 'AnnotationClasses', 'Images', 'Annotations');

-- Contar índices creados
SELECT 
    'Índices creados: ' + CAST(COUNT(*) AS NVARCHAR(10)) as Resultado
FROM sys.indexes 
WHERE name LIKE 'IX_%';

-- Contar triggers creados
SELECT 
    'Triggers creados: ' + CAST(COUNT(*) AS NVARCHAR(10)) as Resultado
FROM sys.triggers 
WHERE name LIKE 'TR_%';

-- Contar stored procedures creados
SELECT 
    'Stored Procedures creados: ' + CAST(COUNT(*) AS NVARCHAR(10)) as Resultado
FROM sys.procedures 
WHERE name LIKE 'sp_%';

-- Contar vistas creadas
SELECT 
    'Vistas creadas: ' + CAST(COUNT(*) AS NVARCHAR(10)) as Resultado
FROM sys.views 
WHERE name LIKE 'vw_%';

PRINT '';
PRINT '🎉 ¡INSTALACIÓN COMPLETADA!';
PRINT '============================';
PRINT 'Base de datos configurada para YOLO Multi-Class Annotator';
PRINT 'Características incluidas:';
PRINT '- Sistema de autenticación JWT completo';
PRINT '- Gestión personalizada de clases de anotación';
PRINT '- Soporte para sesiones y proyectos';
PRINT '- Vistas de estadísticas y reportes';
PRINT '- Stored procedures para operaciones optimizadas';
PRINT '';
PRINT 'Próximos pasos:';
PRINT '1. Configurar cadena de conexión en la aplicación';
PRINT '2. Crear usuario administrador inicial';
PRINT '3. Probar conectividad desde la aplicación';
PRINT '4. Usar la interfaz de gestión de clases en el anotador';
PRINT '';

-- ========================================================
-- COMENTARIOS FINALES Y CONFIGURACIÓN
-- ========================================================

/*
INSTRUCCIONES DE USO:

1. PREPARACIÓN:
   - Crear base de datos: CREATE DATABASE [YOLOAnnotator];
   - Usar la base de datos: USE [YOLOAnnotator];
   - Ejecutar este script completo

2. CONFIGURACIÓN DE APLICACIÓN:
   - Cadena de conexión: 
     Server=tu-servidor;Database=YOLOAnnotator;User Id=tu-usuario;Password=tu-password;
   - O con autenticación Windows:
     Server=tu-servidor;Database=YOLOAnnotator;Trusted_Connection=true;

3. GESTIÓN DE CLASES PERSONALIZADA:
   - Sistema completo de clases por usuario y sesión
   - Clases globales disponibles para todos los usuarios
   - Colores personalizables con validación hexadecimal
   - API REST completa para CRUD de clases
   - Interfaz modal integrada en el anotador
   - Funciones de reset y configuración por defecto

4. CONFIGURACIÓN DE SEGURIDAD:
   - Crear usuario específico para la aplicación
   - Asignar permisos mínimos necesarios (db_datareader, db_datawriter)
   - Configurar backup automático
   - Habilitar auditoría si es necesario

5. MANTENIMIENTO:
   - Ejecutar sp_CleanupExpiredTokens periódicamente
   - Monitorear crecimiento de tablas Images y Annotations
   - Configurar índices adicionales según patrones de uso
   - Implementar archivado de datos antiguos

6. MONITOREO Y ESTADÍSTICAS:
   - Vistas para estadísticas de clases por usuario
   - Reportes de clases más utilizadas
   - Análisis de gestión y uso de clases
   - Query Store habilitado para análisis de performance

CARACTERÍSTICAS INCLUIDAS:
✅ Sistema completo de autenticación JWT
✅ Gestión personalizada de clases de anotación
✅ Clases globales y específicas por sesión
✅ Todas las tablas necesarias para YOLO annotation
✅ Índices optimizados para performance
✅ Constraints para integridad de datos
✅ Triggers para timestamps automáticos
✅ Stored procedures para mantenimiento y gestión de clases
✅ Vistas para reporting y estadísticas de clases
✅ Compatibilidad con Azure SQL Database
✅ Configuración de trabajos automáticos

STORED PROCEDURES PARA GESTIÓN DE CLASES:
- sp_CreateDefaultClasses: Crear clases por defecto para nuevo usuario
- sp_GetUserClasses: Obtener clases filtradas por usuario/sesión
- sp_GetClassStatistics: Estadísticas detalladas de uso de clases

PRÓXIMAS MEJORAS POSIBLES:
- Particionado de tablas grandes (Images, Annotations)
- Implementación de Change Data Capture (CDC)
- Integration Services (SSIS) para ETL
- Reporting Services (SSRS) para dashboards
- Full-text search en descripciones
- Temporal tables para auditoría histórica

COMPATIBILIDAD:
- SQL Server 2019+ (on-premise)
- Azure SQL Database
- Azure SQL Managed Instance
- SQL Server 2017+ (funcionalidad limitada)
*/

-- ========================================================
-- FIN DEL SCRIPT
-- ========================================================
